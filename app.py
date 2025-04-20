from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from database import get_db
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
from werkzeug.serving import is_running_from_reloader

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_123!'  # Changez ceci en production
ITEMS_PER_PAGE = 20

# Configuration
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Désactive le cache en développement

# Route pour favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', 
                             mimetype='image/vnd.microsoft.icon')

@app.route('/')
def dashboard():
    conn = get_db()
    try:
        # Récupération avec filtres
        date_debut = request.args.get('date_debut')
        date_fin = request.args.get('date_fin')
        ligne = request.args.get('ligne')
        
        query = "SELECT * FROM plateaux"
        conditions = []
        params = []
        
        if date_debut:
            conditions.append("date >= ?")
            params.append(date_debut)
        if date_fin:
            conditions.append("date <= ?")
            params.append(date_fin)
        if ligne:
            conditions.append("ligne = ?")
            params.append(ligne)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY date DESC LIMIT 1000"
        
        df = pd.read_sql(query, conn, params=params if params else None)
        
        # Messages flash
        if request.args.get('success'):
            flash('Nouveau plateau enregistré avec succès!', 'success')
        
        # Préparation des données
        stats = {
            'total': round(df['poids'].sum(), 2) if not df.empty else 0,
            'moyenne': round(df['poids'].mean(), 2) if not df.empty else 0,
            'top_op': df.groupby('id_operatrice')['poids'].sum().idxmax() if not df.empty else "N/A",
            'count': len(df)
        }

        # Graphiques (seulement si des données existent)
        if not df.empty:
            fig1 = px.line(
                df.groupby('date')['poids'].sum().reset_index(),
                x='date', y='poids',
                title='Production Journalière (kg)',
                labels={'poids': 'Poids (kg)', 'date': 'Date'},
                color_discrete_sequence=['#3498db']
            )
            
            fig2 = px.bar(
                df.groupby('id_operatrice')['poids'].sum().nlargest(10).reset_index(),
                x='id_operatrice', y='poids',
                title='Top 10 Opératrices',
                labels={'poids': 'Poids total (kg)', 'id_operatrice': 'Opératrice'},
                color_discrete_sequence=['#2ecc71']
            )
            
            graph1 = fig1.to_html(full_html=False)
            graph2 = fig2.to_html(full_html=False)
        else:
            graph1 = graph2 = "<div class='alert alert-info'>Aucune donnée à afficher</div>"

        return render_template('dashboard.html',
                            stats=stats,
                            graph1=graph1,
                            graph2=graph2,
                            title="Tableau de Bord",
                            current_filters={
                                'date_debut': date_debut,
                                'date_fin': date_fin,
                                'ligne': ligne
                            })
    
    except Exception as e:
        flash(f"Erreur technique: {str(e)}", 'danger')
        return render_template('error.html',
                             message="Une erreur est survenue",
                             title="Erreur")
    finally:
        conn.close()

@app.route('/add', methods=['GET'])
def show_add_form():
    return render_template('add.html', 
                         title="Ajouter un plateau",
                         today=datetime.now().strftime('%Y-%m-%d'))

@app.route('/add', methods=['POST'])
def add_record():
    conn = get_db()
    try:
        data = {
            'date': request.form['date'],
            'ligne': int(request.form['ligne']),
            'id_operatrice': request.form['id_operatrice'].upper(),
            'poids': float(request.form['poids'])
        }
        
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO plateaux (date, ligne, id_operatrice, poids) VALUES (?, ?, ?, ?)",
            (data['date'], data['ligne'], data['id_operatrice'], data['poids'])
        )
        conn.commit()
        
        flash('Plateau ajouté avec succès!', 'success')
        return redirect(url_for('dashboard'))
    
    except ValueError:
        flash('Veuillez entrer des valeurs valides', 'danger')
        return redirect(url_for('show_add_form'))
    except Exception as e:
        conn.rollback()
        flash(f"Erreur lors de l'ajout: {str(e)}", 'danger')
        return redirect(url_for('show_add_form'))
    finally:
        conn.close()

@app.route('/api/data')
def api_data():
    """Endpoint pour datatables ou autres"""
    conn = get_db()
    try:
        page = int(request.args.get('page', 1))
        offset = (page - 1) * ITEMS_PER_PAGE
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM plateaux ORDER BY date DESC LIMIT ? OFFSET ?",
            (ITEMS_PER_PAGE, offset)
        )
        
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return jsonify({
            "data": data,
            "page": page,
            "total": len(data)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    if not is_running_from_reloader():
        print("\n=== Suivi de Production ===")
        print("Local:   http://127.0.0.1:5000")
        print("Réseau:  http://192.168.61.32:5000")
        print("CTRL+C pour arrêter\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)