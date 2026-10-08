#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::{io::{BufRead,BufReader,Write},process::{Child,ChildStdin,Command,Stdio},sync::{Mutex,Arc,mpsc,atomic::{AtomicBool,Ordering}}};
use tauri::{Manager,State,WebviewUrl,WebviewWindowBuilder};
use serde_json::{Value,json};
struct Backend{child:Child,input:ChildStdin,output:mpsc::Receiver<String>}
struct Shared(Arc<Mutex<Option<Backend>>>);
struct Minimized(AtomicBool);
struct TranscriptEnabled(AtomicBool);
struct PillEnabled(AtomicBool);
fn transcript_file(app:&tauri::AppHandle)->Result<std::path::PathBuf,String>{let dir=app.path().app_config_dir().map_err(|e|e.to_string())?;std::fs::create_dir_all(&dir).map_err(|e|e.to_string())?;Ok(dir.join("transcript-overlay.json"))}
fn save_transcript(app:&tauri::AppHandle,enabled:bool)->Result<(),String>{std::fs::write(transcript_file(app)?,json!({"enabled":enabled}).to_string()).map_err(|e|e.to_string())?;app.state::<TranscriptEnabled>().0.store(enabled,Ordering::SeqCst);Ok(())}
fn backend()->Result<Backend,String>{
 let exe=std::env::current_exe().map_err(|e|e.to_string())?;
 let base=exe.parent().ok_or("Missing app directory")?;
 let frozen=base.join("backend/jarvis-local-core.exe");
 if !frozen.exists(){return Err("Bundled local core missing. Extract the entire JARVIS Windows folder, not just its EXE.".into())}
 // Fixed packaged executable only. Never falls back to system Python or a renderer path.
 let mut cmd=Command::new(frozen);cmd.stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null());
 #[cfg(windows)]{use std::os::windows::process::CommandExt;cmd.creation_flags(0x08000000);}
 let mut child=cmd.spawn().map_err(|_|"Bundled local core could not start. Extract the full ZIP and check Windows security notices.".to_string())?;
 let input=child.stdin.take().ok_or("Missing input")?;let stdout=child.stdout.take().ok_or("Missing output")?;let(tx,output)=mpsc::channel();std::thread::spawn(move||{for line in BufReader::new(stdout).lines(){match line {Ok(s)=>{if tx.send(s).is_err(){break}},Err(_)=>break}}});Ok(Backend{child,input,output})
}
#[tauri::command]
async fn bridge(request:Value,state:State<'_,Shared>)->Result<Value,String>{
 let state=state.0.clone();tauri::async_runtime::spawn_blocking(move||exchange(request,state)).await.map_err(|_|"Backend task failed".to_string())?
}
fn exchange(request:Value,state:Arc<Mutex<Option<Backend>>>)->Result<Value,String>{
 let command=request.get("command").and_then(Value::as_str).ok_or("Invalid command")?;
 if !["sheets-write-prepare","sheets-write-submit","sheets-write-stop","github-issue-prepare","github-issue-submit","github-issue-stop","source-answer-prepare","source-answer-start","source-answer-stop","phone-transport-prepare","phone-transport-start","phone-pair-open","brain-switch-prepare","brain-switch-apply","brain-switch-stop","watch-windows","watch-start","watch-stop","reflex-mode","reflex-preview","reflex-stop","invoice-open","invoice-prepare","invoice-save","invoice-stop","telegram-voice-prepare","telegram-output-prepare","telegram-output-submit","telegram-output-stop","telegram-resume","telegram-configure","telegram-pair","telegram-approve","telegram-stop","gcal-prepare","gcal-submit","gcal-stop","gcal-reconcile","gmail-prepare","gmail-submit","gmail-stop","gmail-reconcile","focus-prepare","focus-start","focus-pause","focus-resume","focus-finish","focus-stop","projects-connect", "projects-read", "projects-stop", "projects-disconnect", "google-read","google-read-stop","google-configure","google-connect","google-stop","google-disconnect","phone-stop","phone-pair-approve","agent-create","agent-nodes","apps","awareness-mode","brain-check","brain-models","brain-save","brain-warmup","browser-enable","browser-links","browser-mode","browser-preview","browser-run","browser-select","browser-stop","calendar-cancel","calendar-open","calendar-open-preview","calendar-preview","calendar-save","camera-off","camera-on","camera-vision","canvas-open","canvas-open-preview","chat","close","conversation-interrupt","desktop-cancel","desktop-mode","desktop-preview","desktop-run","desktop-task-preview","desktop-task-run","desktop-task-stop","desktop-windows","embedding-check","embedding-setup","embedding-stop","embedding2-select","embedding2-check","embedding2-links","embedding2-search","embedding2-setup","embedding2-stop","evolution-cancel","evolution-export","evolution-generate","game-enable","game-stop","game-windows","history-clear","history-delete","history-list","history-new","history-open","idle-activity","idle-mode","judgment","key-delete","key-save","knowledge-read","knowledge-search","knowledge-speak","knowledge-stop","laya-cancel","laya-check","laya-load","laya-mode","laya-propose","laya-session","laya-setup","laya-stop","local-speed","local-speed-stop","news-cancel","news-open","news-preview","news-speak","news-stop","news-text","obsidian-create","obsidian-disable","obsidian-open","obsidian-sync","pause","plan-cancel","plan-open","plan-preview","presence-mode","proactive-session","select","specialist-configure","specialist-models","specialist-run","specialist-stop","status","team-dialogue","team-round","teammate-awareness","turn-cancel","turn-check","turn-mode","turn-setup","vault-connect","vault-create","vault-disconnect","vault-preview","vault-read","vault-search","vault-semantic","vault-semantic-stop","voice-cancel","voice-check","voice-endpoint","voice-engine","voice-off","voice-on","voice-setup"].contains(&command){return Err("Unknown command".into())}
 let line=serde_json::to_string(&request).map_err(|_|"Invalid request")?;if line.len()>30000{return Err("Request too large".into())}
 let mut guard=state.lock().map_err(|_|"Backend busy")?;if guard.is_none(){*guard=Some(backend()?)}
 let b=guard.as_mut().ok_or("Backend unavailable")?;writeln!(b.input,"{}",line).map_err(|_|"Backend stopped")?;b.input.flush().map_err(|_|"Backend stopped")?;
 let reply=match b.output.recv_timeout(std::time::Duration::from_secs(3)){Ok(s)=>s,Err(_)=>{let _=b.child.kill();*guard=None;return Err("Backend timed out/stopped; sensing released. Reconnect required.".into())}};
 if reply.len()>8_000_000{return Err("Response too large".into())}
 serde_json::from_str(&reply).map_err(|_|"Invalid backend response".into())
}
fn sync_captions(app:&tauri::AppHandle)->Result<(),String>{
 let workspace_open=if let Some(w)=app.get_webview_window("main"){w.is_visible().map_err(|e|e.to_string())?&&!w.is_minimized().map_err(|e|e.to_string())?}else{false};
 if let Some(p)=app.get_webview_window("pill"){if app.state::<PillEnabled>().0.load(Ordering::SeqCst)&&!workspace_open{p.show().map_err(|e|e.to_string())?}else{p.hide().map_err(|e|e.to_string())?}}
 let enabled=app.state::<TranscriptEnabled>().0.load(Ordering::SeqCst);
 if let Some(c)=app.get_webview_window("captions"){if enabled&&!workspace_open{c.show().map_err(|e|e.to_string())?}else{c.hide().map_err(|e|e.to_string())?}}
 Ok(())
}
// Close owns the hidden-workspace transition. Do not re-read visibility mid-hide.
fn show_background_windows(app:&tauri::AppHandle)->Result<(),String>{
 if let Some(p)=app.get_webview_window("pill"){if app.state::<PillEnabled>().0.load(Ordering::SeqCst){p.show().map_err(|e|e.to_string())?}else{p.hide().map_err(|e|e.to_string())?}}
 if let Some(c)=app.get_webview_window("captions"){if app.state::<TranscriptEnabled>().0.load(Ordering::SeqCst){c.show().map_err(|e|e.to_string())?}else{c.hide().map_err(|e|e.to_string())?}}
 Ok(())
}
fn ensure_captions(app:&tauri::AppHandle)->Result<(),String>{
 if app.get_webview_window("captions").is_none(){
  let monitor=app.primary_monitor().map_err(|e|e.to_string())?.ok_or("Display unavailable")?;let scale=monitor.scale_factor();let screen=monitor.size();let origin=monitor.position();let width=380.;let height=(screen.height as f64/scale*0.58).min(580.);
  WebviewWindowBuilder::new(app,"captions",WebviewUrl::App("index.html?caption".into())).initialization_script("window.__JARVIS_CAPTION__ = true; document.documentElement.classList.add('caption-root');").title("JARVIS / Live captions").inner_size(width,height).position(origin.x as f64/scale+screen.width as f64/scale-width-24.,origin.y as f64/scale+(screen.height as f64/scale-height)/2.).decorations(false).shadow(false).no_redirection_bitmap(true).resizable(false).transparent(true).always_on_top(true).focused(false).visible(false).build().map_err(|e|e.to_string())?;
 }Ok(())
}
fn ensure_pill(app:&tauri::AppHandle)->Result<(),String>{
 if app.get_webview_window("pill").is_none(){
  let monitor=app.primary_monitor().map_err(|e|e.to_string())?.ok_or("Display unavailable")?;let scale=monitor.scale_factor();let screen=monitor.size();let origin=monitor.position();let width=240.;let height=40.;
  let pos=(origin.x as f64/scale+(screen.width as f64/scale-width)/2.,origin.y as f64/scale+2.);
  WebviewWindowBuilder::new(app,"pill",WebviewUrl::App("index.html?pill".into())).initialization_script("document.documentElement.classList.add('pill-root');").title("JARVIS / Compact voice bar").inner_size(width,height).position(pos.0,pos.1).decorations(false).shadow(false).no_redirection_bitmap(true).resizable(false).transparent(true).always_on_top(true).focused(false).visible(false).build().map_err(|e|e.to_string())?;
 }Ok(())
}
#[tauri::command]
async fn pill_drag(app:tauri::AppHandle)->Result<(),String>{app.get_webview_window("pill").ok_or("Compact bar missing")?.start_dragging().map_err(|e|e.to_string())}
#[tauri::command]
async fn pill_mode(app:tauri::AppHandle,enabled:bool)->Result<(),String>{let path=app.path().app_config_dir().map_err(|e|e.to_string())?.join("pill-enabled.json");std::fs::write(path,json!({"enabled":enabled}).to_string()).map_err(|e|e.to_string())?;app.state::<PillEnabled>().0.store(enabled,Ordering::SeqCst);sync_captions(&app)}
#[tauri::command]
async fn overlay(app:tauri::AppHandle)->Result<bool,String>{ensure_captions(&app)?;save_transcript(&app,true)?;sync_captions(&app)?;Ok(app.state::<TranscriptEnabled>().0.load(Ordering::SeqCst))}
#[tauri::command]
async fn resize_faces(size:String)->Result<(),String>{if ["small","medium","large"].contains(&size.as_str()){Ok(())}else{Err("Invalid face size".into())}}
#[tauri::command]
async fn floating_status(app:tauri::AppHandle)->Result<f64,String>{sync_captions(&app)?;Ok(0.)}
#[tauri::command]
async fn floating_off(app:tauri::AppHandle)->Result<bool,String>{save_transcript(&app,false)?;if let Some(w)=app.get_webview_window("main"){w.unminimize().map_err(|e|e.to_string())?;w.show().map_err(|e|e.to_string())?;}sync_captions(&app)?;Ok(app.state::<TranscriptEnabled>().0.load(Ordering::SeqCst))}
#[tauri::command]
async fn workspace(app:tauri::AppHandle)->Result<(),String>{let w=app.get_webview_window("main").ok_or("Workspace missing")?;w.unminimize().map_err(|e|e.to_string())?;w.show().map_err(|e|e.to_string())?;w.set_focus().map_err(|e|e.to_string())?;sync_captions(&app)?;Ok(())}
#[tauri::command]
async fn drag_faces(app:tauri::AppHandle)->Result<(),String>{app.get_webview_window("faces").ok_or("Faces missing")?.start_dragging().map_err(|e|e.to_string())}
fn main(){tauri::Builder::default().manage(Shared(Arc::new(Mutex::new(None)))).manage(Minimized(AtomicBool::new(false))).manage(TranscriptEnabled(AtomicBool::new(true))).manage(PillEnabled(AtomicBool::new(true))).setup(|app|{let enabled=transcript_file(app.handle()).ok().and_then(|p|std::fs::read_to_string(p).ok()).and_then(|s|serde_json::from_str::<Value>(&s).ok()).and_then(|v|v.get("enabled").and_then(Value::as_bool)).unwrap_or(true);app.state::<TranscriptEnabled>().0.store(enabled,Ordering::SeqCst);let pill=app.path().app_config_dir().ok().and_then(|p|std::fs::read_to_string(p.join("pill-enabled.json")).ok()).and_then(|s|serde_json::from_str::<Value>(&s).ok()).and_then(|v|v.get("enabled").and_then(Value::as_bool)).unwrap_or(true);app.state::<PillEnabled>().0.store(pill,Ordering::SeqCst);ensure_pill(app.handle()).map_err(std::io::Error::other)?;ensure_captions(app.handle()).map_err(std::io::Error::other)?;Ok(())}).on_window_event(|window,event|{if window.label()=="main" {if let tauri::WindowEvent::CloseRequested{api,..}=event{if window.state::<TranscriptEnabled>().0.load(Ordering::SeqCst){api.prevent_close();if let Err(e)=window.hide(){eprintln!("Workspace hide failed: {}",e);}else if let Err(e)=show_background_windows(window.app_handle()){eprintln!("Transcript close transition failed: {}",e);}}else{api.prevent_close();window.app_handle().exit(0);}}if let tauri::WindowEvent::Resized(_)=event{let minimized=window.is_minimized().unwrap_or(false);let was=window.state::<Minimized>().0.swap(minimized,Ordering::SeqCst);if minimized&&!was{let app=window.app_handle().clone();tauri::async_runtime::spawn(async move{if let Err(e)=sync_captions(&app){eprintln!("Transcript overlay unavailable: {}",e);}});}}}else if window.label()=="pill"{if let tauri::WindowEvent::Moved(position)=event{let scale=window.scale_factor().unwrap_or(1.);if let Ok(dir)=window.app_handle().path().app_config_dir(){let _=std::fs::write(dir.join("pill-position.json"),json!({"x":position.x as f64/scale,"y":position.y as f64/scale}).to_string());}}if let tauri::WindowEvent::CloseRequested{api,..}=event{api.prevent_close();let _=window.hide();}}else if window.label()=="captions"{if let tauri::WindowEvent::CloseRequested{api,..}=event{api.prevent_close();let _=save_transcript(window.app_handle(),false);if let Some(w)=window.app_handle().get_webview_window("main"){let _=w.unminimize();let _=w.show();}let _=window.hide();}}}).invoke_handler(tauri::generate_handler![bridge,overlay,floating_status,floating_off,workspace,drag_faces,resize_faces,pill_drag,pill_mode]).build(tauri::generate_context!()).expect("JARVIS UI failed").run(|app,event|{if let tauri::RunEvent::Exit=event {if let Ok(mut guard)=app.state::<Shared>().0.lock(){if let Some(b)=guard.as_mut(){let _=writeln!(b.input,"{}",json!({"command":"close"}));let _=b.input.flush();let _=b.output.recv_timeout(std::time::Duration::from_secs(2));let _=b.child.kill();}}}});}
