"""
Script xóa dữ liệu test burst habit cho Zalo
Xóa các bản ghi app_usage_logs của Zalo trong ngày hôm nay
"""

import sys
import sqlite3
from pathlib import Path

workspace_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(workspace_root))

from database.db_manager import get_db_manager

def cleanup_zalo_test_data():
    db = get_db_manager()
    
    print("=" * 50)
    print("  XOA DU LIEU TEST ZALO")
    print("=" * 50)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Xoa app_usage_logs cua Zalo trong hom nay
        cursor.execute("""
            DELETE FROM app_usage_logs 
            WHERE tenUngDung LIKE '%zalo%' 
            AND DATE(thoiGianMo) = DATE('now')
        """)
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"  Da xoa: {deleted_count} ban ghi app_usage_logs cua Zalo")
        
        # Kiem tra con lai
        cursor.execute("""
            SELECT COUNT(*) FROM app_usage_logs 
            WHERE tenUngDung LIKE '%zalo%' 
            AND DATE(thoiGianMo) = DATE('now')
        """)
        remaining = cursor.fetchone()[0]
        print(f"  Con lai: {remaining} ban ghi")
    
    print("=" * 50)
    print("  HOAN TAT!")

def check_app_usage():
    """Kiem tra du lieu su dung app hom nay"""
    db = get_db_manager()
    
    print("\n" + "=" * 50)
    print("  KIEM TRA DU LIEU APP USAGE HOM NAY")
    print("=" * 50)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Xem cac ung dung trong app_usage_logs hom nay
        cursor.execute("""
            SELECT DISTINCT tenUngDung, COUNT(*) as so_lan 
            FROM app_usage_logs 
            WHERE DATE(thoiGianMo) = DATE('now')
            GROUP BY tenUngDung
        """)
        print("Ung dung trong ngay hom nay:")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"  {row[0]}: {row[1]} lan")
        else:
            print("  Khong co du lieu")
        
        # Kiem tra tong so ban ghi
        cursor.execute("SELECT COUNT(*) FROM app_usage_logs")
        total = cursor.fetchone()[0]
        print(f"\nTong so ban ghi: {total}")
    
    print("=" * 50)

def check_all_zalo_data():
    """Kiem tra tat ca du lieu Zalo trong database"""
    db = get_db_manager()
    
    print("\n" + "=" * 50)
    print("  KIEM TRA Tat ca DU LIEU ZALO")
    print("=" * 50)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Liet ke tat ca cac bang
        print("\n[0] CAC BANG TRONG DATABASE:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for row in cursor.fetchall():
            print(f"  {row[0]}")
        
        # Kiem tra user_habits
        print("\n[1] USER_HABITS (zalo):")
        cursor.execute("SELECT * FROM user_habits WHERE tenMucTieu LIKE '%zalo%'")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"  {row}")
        else:
            print("  Khong co du lieu")
        
        # Kiem tra suggestions (neu bang ton tai)
        print("\n[2] SUGGESTIONS (zalo):")
        try:
            cursor.execute("SELECT * FROM suggestions WHERE message LIKE '%zalo%'")
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    print(f"  {row}")
            else:
                print("  Khong co du lieu")
        except sqlite3.OperationalError:
            print("  Bang suggestions khong ton tai")
        
        # Kiem tra app_usage_logs (tat ca)
        print("\n[3] APP_USAGE_LOGS (zalo - tat ca):")
        cursor.execute("SELECT COUNT(*) FROM app_usage_logs WHERE tenUngDung LIKE '%zalo%'")
        count = cursor.fetchone()[0]
        print(f"  Tong so ban ghi: {count}")
        
        # Xoa tat ca du lieu Zalo
        print("\n[4] XOA TAT CA DU LIEU ZALO:")
        cursor.execute("DELETE FROM app_usage_logs WHERE tenUngDung LIKE '%zalo%'")
        deleted = cursor.rowcount
        conn.commit()
        print(f"  Da xoa: {deleted} ban ghi")
        
        cursor.execute("DELETE FROM user_habits WHERE tenMucTieu LIKE '%zalo%'")
        deleted = cursor.rowcount
        conn.commit()
        print(f"  Da xoa user_habits: {deleted} ban ghi")
        
        # Xoa suggestions (neu bang ton tai)
        print("\n[5] XOA SUGGESTIONS (zalo):")
        try:
            cursor.execute("DELETE FROM suggestions WHERE message LIKE '%zalo%'")
            deleted = cursor.rowcount
            conn.commit()
            print(f"  Da xoa suggestions: {deleted} ban ghi")
        except sqlite3.OperationalError:
            print("  Bang suggestions khong ton tai, bo qua")
    
    print("\n" + "=" * 50)
    print("  HOAN TAT!")
    print("=" * 50)

if __name__ == '__main__':
    cleanup_zalo_test_data()
    check_app_usage()
    check_all_zalo_data()