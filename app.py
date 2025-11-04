import psycopg2
from flask import Flask, render_template, request, redirect, url_for

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
DB_CONFIG = {
    "host": "localhost",
    "port": 6000,
    "database": "playlistdb",
    "user": "postgres",
    "password": "0000"
}

app = Flask(__name__)

# --- FUNÇÕES AUXILIARES DE CONEXÃO E DB ---

def get_conn():
    """Retorna uma nova conexão com o PostgreSQL."""
    return psycopg2.connect(**DB_CONFIG)

def fetch_all_musicas():
    """Busca e retorna todas as músicas da tabela."""
    conn = get_conn()
    musicas = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, titulo, artista, genero, duracao_seconds, ano FROM musicas ORDER BY id DESC")
            # Obter os nomes das colunas
            col_names = [desc[0] for desc in cur.description]
            # Mapear resultados para dicionários
            for row in cur.fetchall():
                musicas.append(dict(zip(col_names, row)))
    except psycopg2.Error as e:
        print(f"Erro ao buscar músicas: {e}")
    finally:
        conn.close()
    return musicas

def inserir_musica(titulo, artista, genero, duracao, ano):
    """Insere uma música no banco de dados."""
    query = """
        INSERT INTO musicas (titulo, artista, genero, duracao_seconds, ano)
        VALUES (%s, %s, %s, %s, %s);
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, (titulo, artista, genero, duracao, ano))
    except psycopg2.Error as e:
        print(f"Erro ao inserir música: {e}")
    finally:
        conn.close()

def deletar_musica(musica_id):
    """Deleta uma música pelo ID."""
    query = "DELETE FROM musicas WHERE id = %s;"
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, (musica_id,))
    except psycopg2.Error as e:
        print(f"Erro ao deletar música: {e}")
    finally:
        conn.close()


# --- ROTAS WEB (O MENU DE GERENCIAMENTO) ---

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Rota principal:
    GET: Visualiza todos os dados e o formulário de adição.
    POST: Processa o envio do formulário (CREATE).
    """
    
    if request.method == 'POST':
        # 1. Coleta dados do formulário HTML
        titulo = request.form['titulo']
        artista = request.form['artista']
        genero = request.form['genero']
        
        # Converte a duração e ano para inteiro, lidando com valores vazios
        try:
            duracao = int(request.form['duracao']) if request.form['duracao'] else None
        except ValueError:
            duracao = None
            
        try:
            ano = int(request.form['ano']) if request.form['ano'] else None
        except ValueError:
            ano = None

        # 2. Insere no banco
        inserir_musica(titulo, artista, genero, duracao, ano)
        
        # 3. Redireciona para a mesma página para evitar envio duplicado
        return redirect(url_for('index'))

    # GET: Busca todos os dados para visualização
    musicas = fetch_all_musicas()
    return render_template('index.html', musicas=musicas)

@app.route('/delete/<int:musica_id>', methods=['POST'])
def delete_musica(musica_id):
    """
    Rota para deletar um item específico.
    """
    deletar_musica(musica_id)
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Roda a aplicação Flask
    app.run(debug=True)