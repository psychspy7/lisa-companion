import unittest,subprocess,sys
from pathlib import Path
from offline_companion import bounded_prompt
class OfflineBudget(unittest.TestCase):
 def test_long_multilingual_context_stays_inside_total_budget(self):
  prompt=bounded_prompt('Lisa system '*30,'हिन्दी'*1000,[{'role':'user','content':'long '*4000}]*8,['note '*1000]*50,True)
  self.assertLessEqual(len(prompt.encode('utf-8')),1700)
  self.assertTrue(prompt.endswith('<|im_start|>assistant\n'))
  self.assertIn('हिन्दी',prompt)
 def test_owner_tool_help_runs_from_direct_script_entry(self):
  root=Path(__file__).resolve().parents[1]
  p=subprocess.run([sys.executable,str(root/'tools/manage_activation.py'),'--help'],cwd=root,capture_output=True,timeout=15)
  self.assertEqual(p.returncode,0,p.stderr.decode(errors='replace'))
