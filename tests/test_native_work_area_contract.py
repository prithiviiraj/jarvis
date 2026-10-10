import pathlib,unittest
R=pathlib.Path(__file__).resolve().parents[1]
class WorkAreaContract(unittest.TestCase):
 def test_native_fits_work_area_in_physical_pixels_before_launch(self):
  s=(R/'modern-ui/src-tauri/src/main.rs').read_text();body=s.split('fn fit_workspace(',1)[1].split('fn ensure_captions',1)[0]
  for term in ('monitor.work_area()','w.inner_size()','w.outer_size()','saturating_sub','w.set_min_size','w.set_size','w.set_position','tauri::PhysicalSize','area.position'):
   self.assertIn(term,body)
  self.assertIn('.setup(|app|{create_workspace(app.handle())',s)
  import json
  self.assertFalse(json.loads((R/'modern-ui/src-tauri/tauri.conf.json').read_text())['app']['windows'][0]['create'])
  creation=s.split('fn create_workspace(',1)[1].split('// Fit the decorated workspace',1)[0]
  for term in ('monitor.work_area()','inner_size(width,height)','min_inner_size','visible(false)','fit_workspace(app)?'):
   self.assertIn(term,creation)
 def test_native_acceptance_requires_actual_work_area_not_maximize(self):
  s=(R/'modern-ui/native-smoke.py').read_text()
  for term in ('GetMonitorInfoW','MonitorFromWindow','Workspace outside usable monitor','Master choice outside physical work area'):
   self.assertIn(term,s)
  self.assertNotIn('main.maximize()',s)
