import sqlite3
import os
import json
import argparse
import sys

class CDSDataSkill:
    def __init__(self, db_path=None):
        if db_path:
            self.db_path = db_path
        else:
            # Default path relative to this script
            self.db_path = os.path.join(os.path.dirname(__file__), "Final_Mapping.db")
        
    def _get_connection(self):
        if not os.path.exists(self.db_path):
             raise FileNotFoundError(f"Database not found at {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_cds_fields(self, cds_view_name):
        """
        Get fields for a CDS View.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 2.1: CDS View Name -> CDS Fields
        query = """
            SELECT DISTINCT EntityName, EntityDescription, EntityFieldName, EntityFieldDesc
            FROM Final_Mapping
            WHERE EntityName = ?
        """
        cursor.execute(query, (cds_view_name,))
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "EntityName": row["EntityName"],
                "EntityDescription": row["EntityDescription"],
                "EntityFieldName": row["EntityFieldName"],
                "EntityFieldDesc": row["EntityFieldDesc"]
            })
        return results

    def find_by_ddic_field(self, table_name, field_name):
        """
        Find CDS View by DDIC Table Field.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 2.2: DDIC Table + Field -> CDS View matches
        query = """
            SELECT DISTINCT EntityName, EntityFieldName, EntityFieldDesc
            FROM Final_Mapping
            WHERE TableName = ? AND TableField = ?
        """
        cursor.execute(query, (table_name, field_name))
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "EntityName": row["EntityName"],
                "EntityFieldName": row["EntityFieldName"],
                "EntityFieldDesc": row["EntityFieldDesc"]
            })
        return results

    def find_by_ddic_table(self, table_name):
        """
        Find CDS Views by DDIC Table.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 2.3: DDIC Table -> CDS Views
        # CORRECTED LOGIC: Use tadirObject and tadirObjName to find successors defined in the JSON mapping
        # Group by EntityName to ensure we only get one result per CDS View, selecting the "best" description
        query = """
            SELECT EntityName, MAX(EntityDescription) as EntityDescription
            FROM Final_Mapping
            WHERE tadirObject = 'TABL' AND tadirObjName = ?
            GROUP BY EntityName
        """
        cursor.execute(query, (table_name,))
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "EntityName": row["EntityName"],
                "EntityDescription": row["EntityDescription"]
            })
        return results

# --- Command Handler Functions ---

def cmd_get_cds_fields(args):
    skill = CDSDataSkill()
    result = skill.get_cds_fields(args.cds_view_name)
    print(json.dumps(result, indent=2, ensure_ascii=False))

def cmd_find_by_ddic_field(args):
    skill = CDSDataSkill()
    result = skill.find_by_ddic_field(args.table_name, args.field_name)
    print(json.dumps(result, indent=2, ensure_ascii=False))

def cmd_find_by_ddic_table(args):
    skill = CDSDataSkill()
    result = skill.find_by_ddic_table(args.table_name)
    print(json.dumps(result, indent=2, ensure_ascii=False))

def build_parser():
    parser = argparse.ArgumentParser(description="SAP CDS Mapping Skill Tools")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Action to perform")

    # Command: get_cds_fields
    p_cds = subparsers.add_parser("get_cds_fields", help="Get fields for a CDS View")
    p_cds.add_argument("--cds_view_name", required=True, help="Name of the CDS View")
    p_cds.set_defaults(func=cmd_get_cds_fields)

    # Command: find_by_ddic_field
    p_field = subparsers.add_parser("find_by_ddic_field", help="Find CDS View by DDIC Table Field")
    p_field.add_argument("--table_name", required=True, help="DDIC Table Name")
    p_field.add_argument("--field_name", required=True, help="DDIC Field Name")
    p_field.set_defaults(func=cmd_find_by_ddic_field)

    # Command: find_by_ddic_table
    p_table = subparsers.add_parser("find_by_ddic_table", help="Find CDS Views by DDIC Table")
    p_table.add_argument("--table_name", required=True, help="DDIC Table Name")
    p_table.set_defaults(func=cmd_find_by_ddic_table)
    
    return parser

def main():
    parser = build_parser()
    # Check if no arguments provided, print help
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    try:
        args = parser.parse_args()
        args.func(args)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
