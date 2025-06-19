import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from config import settings  # Import settings module
import logging
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import os

logger = logging.getLogger(__name__)

def export_to_sheet(data, spreadsheet_id, sheet_name):
    try:
        creds = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(spreadsheet_id)

        # Get or create worksheet
        try:
            sheet = spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(
                title=sheet_name,
                rows=max(100, len(data) + 10),
                cols=20
            )

        # Clear all formatting and data (except header)
        sheet.batch_clear(["A2:Z"])  # clear values
        spreadsheet.batch_update({
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet.id
                        },
                        "cell": {
                            "userEnteredFormat": {}  # Clears formatting
                        },
                        "fields": "userEnteredFormat"
                    }
                },
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet.id,
                            "gridProperties": {
                                "frozenRowCount": 0
                            }
                        },
                        "fields": "gridProperties.frozenRowCount"
                    }
                }
            ]
        })

        # Update header to new column order
        header = ["Name", "Role", "Date", "In", "Out", "Leave Status"]
        sheet.update('A1:F1', [header])  # Update header range
        
        if data:
            sheet.append_rows(data)
            
            # Formatting adjustments for new column positions
            spreadsheet.batch_update({
                "requests": [
                    # Header formatting
                    {
                        "repeatCell": {
                            "range": {"sheetId": sheet.id, "startRowIndex": 0, "endRowIndex": 1},
                            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                            "fields": "userEnteredFormat.textFormat.bold"
                        }
                    },
                    # Center align leave status (now in column F)
                    {
                        "repeatCell": {
                            "range": {"sheetId": sheet.id, "startColumnIndex": 5, "endColumnIndex": 6},
                            "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
                            "fields": "userEnteredFormat.horizontalAlignment"
                        }
                    },
                    # Format time columns (In and Out)
                    {
                        "repeatCell": {
                            "range": {
                                "sheetId": sheet.id,
                                "startRowIndex": 1,
                                "endRowIndex": len(data) + 1,
                                "startColumnIndex": 3,  # In column (D)
                                "endColumnIndex": 5    # Out column (E)
                            },
                            "cell": {
                                "userEnteredFormat": {
                                    "numberFormat": {
                                        "type": "TIME"
                                    }
                                }
                            },
                            "fields": "userEnteredFormat.numberFormat"
                        }
                    }
                ]
            })
        return True
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return False
