import pytest
import datetime
from src.core import database as db

@pytest.mark.integration
class TestDatabaseOperations:
    """
    Groups tests that interact with a live database.
    Requires the db_connection fixture from conftest.py.
    """
    def test_add_and_retrieve_outbreak(self, db_connection):
        """
        Tests the full lifecycle of a simple outbreak report: add, retrieve, then delete.
        """
        reporter_name = "Pytest Automated Test"
        woreda_name = "Bena Tsemay" # Assumes this woreda exists from setup
        
        # We will use the main db functions, but need a direct cursor for cleanup
        cur = db_connection.cursor()
        
        try:
            # 1. Add a new outbreak
            success, message = db.add_new_outbreak_report(
                reporter_name=reporter_name,
                woreda_name=woreda_name,
                lat=5.5, lon=36.5, species=["Cattle"],
                complaint="This is a test record.",
                report_date=datetime.date.today()
            )
            assert success is True
            outbreak_id = int(message.split(": ")[-1])
            
            # 2. Retrieve unassigned reports and check if our new one is there
            unassigned_df = db.get_unassigned_reports()
            assert not unassigned_df.empty
            assert outbreak_id in unassigned_df['outbreak_id'].values

            # 3. Assign the outbreak
            success, msg = db.assign_investigator_to_outbreak(outbreak_id, "Test Investigator")
            assert success is True

            # 4. Check it is no longer in the unassigned list
            unassigned_df_after = db.get_unassigned_reports()
            assert outbreak_id not in unassigned_df_after['outbreak_id'].values

        finally:
            # 5. VERY IMPORTANT: Clean up the test data
            print(f"\n[Test DB] Cleaning up test outbreak ID: {outbreak_id}")
            cur.execute("DELETE FROM outbreaks WHERE outbreak_id = %s", (outbreak_id,))
            db_connection.commit()
            cur.close()