#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::{io::{BufRead,BufReader,Write},process::{Child,ChildStdin,Command,Stdio},sync::{Mutex,Arc,mpsc,atomic::{AtomicBool,Ordering}}};
use tauri::{Manager,State,WebviewUrl,WebviewWindowBuilder};
use serde_json::{Value,json};
struct Backend{child:Child,input:ChildStdin,output:mpsc::Receiver<String>}
struct Shared(Arc<Mutex<Option<Backend>>>);
struct Minimized(AtomicBool);
struct TranscriptEnabled(AtomicBool);
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
 if !["status","chat","select","pause","close","camera-on","camera-off","apps","judgment","voice-on","voice-off","voice-setup","voice-check","voice-cancel","brain-save","key-save","key-delete","brain-check","brain-models","brain-warmup","team-round","history-list","history-open","history-new","history-delete","history-clear","vault-connect","vault-disconnect","vault-search","vault-read","vault-create","browser-mode","browser-preview","browser-run","browser-stop","voice-engine","voice-endpoint","browser-links","browser-select","laya-setup","laya-check","laya-load","laya-cancel","laya-mode","laya-propose","laya-stop","camera-vision"].contains(&command){return Err("Unknown command".into())}
 let line=serde_json::to_string(&request).map_err(|_|"Invalid request")?;if line.len()>10000{return Err("Request too large".into())}
 let mut guard=state.lock().map_err(|_|"Backend busy")?;if guard.is_none(){*guard=Some(backend()?)}
 let b=guard.as_mut().ok_or("Backend unavailable")?;writeln!(b.input,"{}",line).map_err(|_|"Backend stopped")?;b.input.flush().map_err(|_|"Backend stopped")?;
 let reply=match b.output.recv_timeout(std::time::Duration::from_secs(3)){Ok(s)=>s,Err(_)=>{let _=b.child.kill();*guard=None;return Err("Backend timed out/stopped; sensing released. Reconnect required.".into())}};
 if reply.len()>8_000_000{return Err("Response too large".into())}
 serde_json::from_str(&reply).map_err(|_|"Invalid backend response".into())
}
fn sync_captions(app:&tauri::AppHandle)->Result<(),String>{
 let workspace_open=if let Some(w)=app.get_webview_window("main"){w.is_visible().map_err(|e|e.to_string())?&&!w.is_minimized().map_err(|e|e.to_string())?}else{false};
 let enabled=app.state::<TranscriptEnabled>().0.load(Ordering::SeqCst);
 if let Some(c)=app.get_webview_window("captions"){if enabled&&!workspace_open{c.show().map_err(|e|e.to_string())?}else{c.hide().map_err(|e|e.to_string())?}}
 Ok(())
}
fn ensure_captions(app:&tauri::AppHandle)->Result<(),String>{
 if app.get_webview_window("captions").is_none(){
  let monitor=app.primary_monitor().map_err(|e|e.to_string())?.ok_or("Display unavailable")?;let scale=monitor.scale_factor();let screen=monitor.size();let origin=monitor.position();let width=380.;let height=(screen.height as f64/scale*0.58).min(580.);
  WebviewWindowBuilder::new(app,"captions",WebviewUrl::App("index.html?caption".into())).initialization_script("window.__JARVIS_CAPTION__ = true; document.documentElement.classList.add('caption-root');").title("JARVIS / Live captions").inner_size(width,height).position(origin.x as f64/scale+screen.width as f64/scale-width-24.,origin.y as f64/scale+(screen.height as f64/scale-height)/2.).decorations(false).shadow(false).no_redirection_bitmap(true).resizable(false).transparent(true).always_on_top(true).focused(false).visible(false).build().map_err(|e|e.to_string())?;
 }Ok(())
}
#[tauri::command]
async fn overlay(app:tauri::AppHandle)->Result<(),String>{ensure_captions(&app)?;save_transcript(&app,true)?;sync_captions(&app)}
#[tauri::command]
async fn resize_faces(size:String)->Result<(),String>{if ["small","medium","large"].contains(&size.as_str()){Ok(())}else{Err("Invalid face size".into())}}
#[tauri::command]
async fn floating_status(app:tauri::AppHandle)->Result<f64,String>{sync_captions(&app)?;Ok(0.)}
#[tauri::command]
async fn floating_off(app:tauri::AppHandle)->Result<(),String>{save_transcript(&app,false)?;if let Some(w)=app.get_webview_window("main"){w.unminimize().map_err(|e|e.to_string())?;w.show().map_err(|e|e.to_string())?;}sync_captions(&app)}
#[tauri::command]
async fn workspace(app:tauri::AppHandle)->Result<(),String>{let w=app.get_webview_window("main").ok_or("Workspace missing")?;w.unminimize().map_err(|e|e.to_string())?;w.show().map_err(|e|e.to_string())?;w.set_focus().map_err(|e|e.to_string())?;sync_captions(&app)?;Ok(())}
#[tauri::command]
async fn drag_faces(app:tauri::AppHandle)->Result<(),String>{app.get_webview_window("faces").ok_or("Faces missing")?.start_dragging().map_err(|e|e.to_string())}
fn main(){tauri::Builder::default().manage(Shared(Arc::new(Mutex::new(None)))).manage(Minimized(AtomicBool::new(false))).manage(TranscriptEnabled(AtomicBool::new(true))).setup(|app|{let enabled=transcript_file(app.handle()).ok().and_then(|p|std::fs::read_to_string(p).ok()).and_then(|s|serde_json::from_str::<Value>(&s).ok()).and_then(|v|v.get("enabled").and_then(Value::as_bool)).unwrap_or(true);app.state::<TranscriptEnabled>().0.store(enabled,Ordering::SeqCst);ensure_captions(app.handle()).map_err(std::io::Error::other)?;Ok(())}).on_window_event(|window,event|{if window.label()=="main" {if let tauri::WindowEvent::CloseRequested{api,..}=event{if window.state::<TranscriptEnabled>().0.load(Ordering::SeqCst){api.prevent_close();let _=window.hide();let _=sync_captions(window.app_handle());}else{api.prevent_close();window.app_handle().exit(0);}}if let tauri::WindowEvent::Resized(_)=event{let minimized=window.is_minimized().unwrap_or(false);let was=window.state::<Minimized>().0.swap(minimized,Ordering::SeqCst);if minimized&&!was{let app=window.app_handle().clone();tauri::async_runtime::spawn(async move{if let Err(e)=sync_captions(&app){eprintln!("Transcript overlay unavailable: {}",e);}});}}}else if window.label()=="captions"{if let tauri::WindowEvent::CloseRequested{api,..}=event{api.prevent_close();let _=save_transcript(window.app_handle(),false);if let Some(w)=window.app_handle().get_webview_window("main"){let _=w.unminimize();let _=w.show();}let _=window.hide();}}}).invoke_handler(tauri::generate_handler![bridge,overlay,floating_status,floating_off,workspace,drag_faces,resize_faces]).build(tauri::generate_context!()).expect("JARVIS UI failed").run(|app,event|{if let tauri::RunEvent::Exit=event {if let Ok(mut guard)=app.state::<Shared>().0.lock(){if let Some(b)=guard.as_mut(){let _=writeln!(b.input,"{}",json!({"command":"close"}));let _=b.input.flush();let _=b.output.recv_timeout(std::time::Duration::from_secs(2));let _=b.child.kill();}}}});}
