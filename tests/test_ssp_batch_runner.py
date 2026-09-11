"""Runner sequencing tests; no Snowflake execution claim."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

P=runpy.run_path(str(Path(__file__).resolve().parents[1] /
                    "notebooks/persistence/PILOT_SSP_TEN_RECORD_BATCH_WRITE.py"))

class BatchRunner(unittest.TestCase):
    def run_case(self, fail_rehearsal=False, fail_final=False):
        fn=P["run_ssp_ten_record_batch"]
        calls,sql,output=[],[],io.StringIO()
        phase={"committed":False}
        def integrity(session,queries,ids,count,allow_absent=False):
            if count == 1:
                return {"NODES":19,"EDGES":18}
            return {"NODES":40 if allow_absent else 30,"EDGES":30 if allow_absent else 20}
        def transaction(session,deletes,merges,before,verify,old,new,commit=False):
            self.assertEqual((40,30),old)
            self.assertEqual((30,20),new)
            calls.append(commit)
            before()
            if fail_rehearsal and not commit:
                raise P["PilotError"]("TRANSACTION_ROLLED_BACK")
            verify(1)
            verify(2)
            phase["committed"]=commit
            return {"STATUS":"COMMITTED" if commit else "ROLLED_BACK"}
        def saved(*a):
            if fail_final and phase["committed"]:
                raise P["PilotError"]("SAVED_VALUES_OR_KEYS_DIFFER_FROM_FROZEN_BATCH")
            return {"MATCHED":True}
        mocks={
            "_pilot_contract":lambda *a:None,"_pilot_no_transaction":lambda *a:None,
            "_pilot_query":lambda s,q:sql.append(q) or [],"_pilot_column_plan":lambda *a:[],
            "_pilot_selection_schema":lambda *a:None,"_batch_freeze":lambda *a:10,
            "_pilot_stage":lambda *a:None,"_batch_integrity":integrity,
            "_batch_overlap_ownership":lambda *a:None,"_pilot_baseline_equal":lambda *a:None,
            "_pilot_merge_sql":lambda *a:"MERGE INTO X","_batch_transaction":transaction,
            "_pilot_verify":saved,
        }
        with patch.dict(fn.__globals__,mocks),redirect_stdout(output):
            if fail_rehearsal or fail_final:
                with self.assertRaises(P["PilotError"]):
                    fn(None,{}, {},None,None,"COMMIT")
                result=json.loads(output.getvalue())
            else:
                result=fn(None,{}, {},None,None,"COMMIT")
        self.assertFalse(any(q.startswith("CREATE TABLE ") for q in sql))
        self.assertTrue(all(q.startswith(("DESC TABLE ","CREATE TEMPORARY TABLE ")) for q in sql))
        return result,calls

    def test_rehearsal_then_commit_and_protected_readback(self):
        result,calls=self.run_case()
        self.assertEqual([False,True],calls)
        self.assertTrue(result["ROLLBACK_RESTORED_BASELINE"])
        self.assertTrue(result["PERSISTED"])
        self.assertTrue(result["READBACK"]["PROTECTED_FIRST_RECORD_UNCHANGED"])
        self.assertEqual("TEN_RECORD_BATCH_COMMITTED_AND_VERIFIED",result["STATUS"])

    def test_failed_rehearsal_never_calls_commit(self):
        result,calls=self.run_case(fail_rehearsal=True)
        self.assertEqual([False],calls)
        self.assertFalse(result["PERSISTED"])
        self.assertTrue(result["FAILURE_ROLLBACK_RESTORED_BASELINE"])

    def test_failed_postcommit_readback_is_not_reported_as_rollback(self):
        result,calls=self.run_case(fail_final=True)
        self.assertEqual([False,True],calls)
        self.assertTrue(result["PERSISTED"])
        self.assertEqual("POST_COMMIT_READBACK",result["PHASE"])
        self.assertNotIn("FAILURE_ROLLBACK_RESTORED_BASELINE",result)

if __name__ == "__main__":
    unittest.main()
