from database import get_db

def afficher_dernieres_entrees(limit=50):
    """Affiche les dernières entrées de la base de données locale"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT * FROM plateaux ORDER BY date DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        
        if not rows:
            print("❌ Aucun plateau trouvé.")
        else:
            print("📝 Derniers plateaux enregistrés :")
            for row in rows:
                print(f"ID: {row[0]}, Date: {row[1]}, Ligne: {row[2]}, Opératrice: {row[3]}, Poids: {row[4]}kg")
    except Exception as e:
        print("❌ Erreur lors de la récupération :", e)
    finally:
        conn.close()

if __name__ == "__main__":
    afficher_dernieres_entrees()