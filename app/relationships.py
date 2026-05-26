ALLOWED_EXPANDS = {
    "SR_Service": {
        "Company": {
            "table": "Company",
            "base_alias": "s",
            "join_alias": "c",
            "left_key": "Company_RecID",
            "right_key": "Company_RecID",
            "default_columns": [
                "Company_RecID",
                "Company_ID",
                "Company_Name",
            ],
        },
        "SR_Status": {
            "table": "SR_Status",
            "base_alias": "s",
            "join_alias": "st",
            "left_key": "SR_Status_RecID",
            "right_key": "SR_Status_RecID",
            "default_columns": [
                "SR_Status_RecID",
                "Description",
                "SR_Board_RecID",
                "Inactive_Flag",
            ],
        },
    }
}