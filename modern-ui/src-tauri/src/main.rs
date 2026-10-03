#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::{io::{BufRead,BufReader,Write},process::{Child,ChildStdin,Command,Stdio},sync::{Mutex,Arc,mpsc},path::PathBuf};
use tauri::{Manager,State,WebviewUrl,WebviewWindowBuilder};
use serde_json::{Value,json};
struct Backend{child:Child,input:ChildStdin,output:mpsc::Receiver<String>}
struct Shared(Arc<Mutex<Option<Backend>>>);
fn backend()->Result<Backend,String>{
 let exe=std::env::current_exe().map_err(|e|e.to_string())?;
 let base=exe.parent().ok_or("Missing app directory")?;
 let source=base.join("backend/src");
 if !source.join("jarvis/ui_bridge.py").exists(){return Err("Local backend files missing. Use the prepared source preview folder.".into())}
 // Fixed Python executable, no renderer-supplied command/path/env arguments.
 let python=base.join("backend/.venv/Scripts/python.exe");
 let launcher=if python.exists(){python}else{PathBuf::from("python")};
 let mut cmd=Command::new(launcher);cmd.args(["-u","-m","jarvis.ui_bridge"]).env("PYTHONPATH",source).stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null());
 #[cfg(windows)]{use std::os::windows::process::CommandExt;cmd.creation_flags(0x08000000);}
 let mut child=cmd.spawn().map_err(|_|"Python backend unavailable. This preview still requires Python/setup.".to_string())?;
 let input=child.stdin.take().ok_or("Missing input")?;let stdout=child.stdout.take().ok_or("Missing output")?;let(tx,output)=mpsc::channel();std::thread::spawn(move||{for line in BufReader::new(stdout).lines(){match line {Ok(s)=>{if tx.send(s).is_err(){break}},Err(_)=>break}}});Ok(Backend{child,input,output})
}
#[tauri::command]
async fn bridge(request:Value,state:State<'_,Shared>)->Result<Value,String>{
 let state=state.0.clone();tauri::async_runtime::spawn_blocking(move||exchange(request,state)).await.map_err(|_|"Backend task failed".to_string())?
}
fn exchange(request:Value,state:Arc<Mutex<Option<Backend>>>)->Result<Value,String>{
 let command=request.get("command").and_then(Value::as_str).ok_or("Invalid command")?;
 if !["status","chat","select","pause","close","camera-on","camera-off","apps","judgment","voice-on","voice-off"].contains(&command){return Err("Unknown command".into())}
 let line=serde_json::to_string(&request).map_err(|_|"Invalid request")?;if line.len()>10000{return Err("Request too large".into())}
 let mut guard=state.lock().map_err(|_|"Backend busy")?;if guard.is_none(){*guard=Some(backend()?)}
 let b=guard.as_mut().ok_or("Backend unavailable")?;writeln!(b.input,"{}",line).map_err(|_|"Backend stopped")?;b.input.flush().map_err(|_|"Backend stopped")?;
 let reply=match b.output.recv_timeout(std::time::Duration::from_secs(3)){Ok(s)=>s,Err(_)=>{let _=b.child.kill();*guard=None;return Err("Backend timed out/stopped; sensing released. Reconnect required.".into())}};
 if reply.len()>100000{return Err("Response too large".into())}
 serde_json::from_str(&reply).map_err(|_|"Invalid backend response".into())
}
#[tauri::command]
async fn overlay(app:tauri::AppHandle)->Result<(),String>{
 if let Some(w)=app.get_webview_window("faces"){w.show().map_err(|e|e.to_string())?;return Ok(())}
 WebviewWindowBuilder::new(&app,"faces",WebviewUrl::App("index.html".into())).initialization_script("window.__JARVIS_OVERLAY__ = true;").title("JARVIS / Floating faces").inner_size(520.,140.).decorations(false).resizable(false).transparent(true).always_on_top(true).build().map_err(|e|e.to_string())?;Ok(())
}
#[tauri::command]
async fn workspace(app:tauri::AppHandle)->Result<(),String>{let w=app.get_webview_window("main").ok_or("Workspace missing")?;w.show().map_err(|e|e.to_string())?;w.set_focus().map_err(|e|e.to_string())?;Ok(())}
#[tauri::command]
async fn drag_faces(app:tauri::AppHandle)->Result<(),String>{app.get_webview_window("faces").ok_or("Faces missing")?.start_dragging().map_err(|e|e.to_string())}
fn main(){tauri::Builder::default().manage(Shared(Arc::new(Mutex::new(None)))).invoke_handler(tauri::generate_handler![bridge,overlay,workspace,drag_faces]).setup(|app|{let handle=app.handle().clone();tauri::async_runtime::spawn(async move{if let Err(error)=overlay(handle.clone()).await{if let Some(w)=handle.get_webview_window("main"){let _=w.show();let _=w.set_title(&format!("JARVIS / Floating setup failed: {}",error));}}});Ok(())}).build(tauri::generate_context!()).expect("JARVIS UI failed").run(|app,event|{if let tauri::RunEvent::Exit=event {if let Ok(mut guard)=app.state::<Shared>().0.lock(){if let Some(b)=guard.as_mut(){let _=writeln!(b.input,"{}",json!({"command":"close"}));let _=b.input.flush();let _=b.output.recv_timeout(std::time::Duration::from_secs(2));let _=b.child.kill();}}}});}
