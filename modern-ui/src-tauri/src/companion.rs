use std::sync::Mutex;
use tauri::{Manager,State,WebviewUrl,WebviewWindowBuilder};
use serde_json::{Value,json};
pub struct Companion(pub Mutex<String>);
pub fn stop(app:tauri::AppHandle,state:State<'_,Companion>)->Result<(),String>{
 *state.0.lock().map_err(|_|"Companion busy")?="off".into();
 if let Some(w)=app.get_webview_window("companion"){w.hide().map_err(|e|e.to_string())?;w.set_ignore_cursor_events(true).map_err(|e|e.to_string())?;}Ok(())
}
#[tauri::command]
pub async fn companion_mode(app:tauri::AppHandle,window:tauri::WebviewWindow,state:State<'_,Companion>,mode:String)->Result<(),String>{
 if window.label()!="main"{return Err("Open the workspace to start the companion".into())}
 if !["off","follow","draw"].contains(&mode.as_str()){return Err("Invalid companion mode".into())}
 stop(app.clone(),state.clone())?;if mode=="off"{return Ok(())}
 let monitor=window.current_monitor().map_err(|e|e.to_string())?.ok_or("Display unavailable")?;
 if app.get_webview_window("companion").is_none(){WebviewWindowBuilder::new(&app,"companion",WebviewUrl::App("index.html?companion".into())).initialization_script("document.documentElement.classList.add('companion-root');").title("JARVIS / Desktop companion").decorations(false).shadow(false).no_redirection_bitmap(true).transparent(true).always_on_top(true).resizable(false).focused(false).visible(false).build().map_err(|e|e.to_string())?;}
 let w=app.get_webview_window("companion").ok_or("Companion unavailable")?;
 w.set_size(*monitor.size()).map_err(|e|e.to_string())?;w.set_position(*monitor.position()).map_err(|e|e.to_string())?;
 w.set_ignore_cursor_events(mode=="follow").map_err(|e|e.to_string())?;
 *state.0.lock().map_err(|_|"Companion busy")?=mode.clone();w.show().map_err(|e|e.to_string())?;
 if mode=="draw"{w.set_focus().map_err(|e|e.to_string())?;}Ok(())
}
#[cfg(windows)]
fn cursor()->Result<(i32,i32),String>{
 #[repr(C)]struct Point{x:i32,y:i32}
 #[link(name="user32")]extern "system"{fn GetCursorPos(point:*mut Point)->i32;}
 let mut point=Point{x:0,y:0};if unsafe{GetCursorPos(&mut point)}==0{return Err("Cursor unavailable".into())}Ok((point.x,point.y))
}
#[cfg(not(windows))]
fn cursor()->Result<(i32,i32),String>{Err("Desktop companion requires Windows".into())}
#[tauri::command]
pub async fn companion_cursor(app:tauri::AppHandle,window:tauri::WebviewWindow,state:State<'_,Companion>)->Result<Value,String>{
 if window.label()!="companion"&&window.label()!="main"{return Err("Companion access only".into())}
 let mode=state.0.lock().map_err(|_|"Companion busy")?.clone();
 if mode!="follow"{return Ok(json!({"mode":mode,"x":0,"y":0}))}
 let w=app.get_webview_window("companion").ok_or("Companion unavailable")?;let origin=w.outer_position().map_err(|e|e.to_string())?;let scale=w.scale_factor().map_err(|e|e.to_string())?;let(x,y)=cursor()?;
 Ok(json!({"mode":mode,"x":(x-origin.x)as f64/scale,"y":(y-origin.y)as f64/scale}))
}

#[tauri::command]
pub async fn companion_stop(app:tauri::AppHandle,state:State<'_,Companion>)->Result<(),String>{stop(app,state)}
