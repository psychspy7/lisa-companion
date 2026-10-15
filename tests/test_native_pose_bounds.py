import json,unittest
from pathlib import Path
class NativePoseBounds(unittest.TestCase):
 def test_squat_excludes_the_previous_standing_feet(self):
  poses=json.loads((Path(__file__).resolve().parents[1]/'godot/assets/poses.json').read_text())
  self.assertGreaterEqual(poses['squat']['rect'][1],1735)
  self.assertLessEqual(poses['squat']['height'],1.30)
 def test_retired_whip_is_not_a_visible_pose(self):
  poses=json.loads((Path(__file__).resolve().parents[1]/'godot/assets/poses.json').read_text())
  self.assertNotIn('whip',poses)
if __name__=='__main__':unittest.main()
