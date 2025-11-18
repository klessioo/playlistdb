import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash
import sys

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
DB_CONFIG = {
    "host": "localhost",
    "port": 6000,
    "database": "playlistdb",
    "user": "postgres",
    "password": "0000"
}

app = Flask(__name__)
# Chave secreta necessária para usar a função flash (mensagens de feedback)
app.secret_key = 'super_secret_key_para_flash' 

# --- FUNÇÕES AUXILIARES DE CONEXÃO E DB ---

def get_conn():
    """Retorna uma nova conexão com o PostgreSQL."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        print(f"ERRO DE CONEXÃO: Não foi possível conectar ao banco de dados com a configuração fornecida. Certifique-se de que o PostgreSQL esteja em execução. Erro: {e}", file=sys.stderr)
        # Retorna None ou levanta a exceção, dependendo da necessidade
        return None

def init_db():
    """Cria as tabelas necessárias (musicas, gravadoras, compositores) se não existirem."""
    conn = get_conn()
    if not conn:
        return
        
    try:
        with conn.cursor() as cur:
            # 1. Tabela Gravadoras
            cur.execute("""
                CREATE TABLE IF NOT EXISTS gravadoras (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL UNIQUE
                );
            """)
            print("Tabela 'gravadoras' verificada/criada.")

            # 2. Tabela Compositores
            cur.execute("""
                CREATE TABLE IF NOT EXISTS compositores (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL UNIQUE
                );
            """)
            print("Tabela 'compositores' verificada/criada.")

            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS musicas (
                    id SERIAL PRIMARY KEY,
                    titulo VARCHAR(255) NOT NULL,
                    artista VARCHAR(255),
                    genero VARCHAR(100),
                    duracao_seconds INTEGER,
                    ano INTEGER,
                    gravadora_id INTEGER REFERENCES gravadoras(id) ON DELETE SET NULL,
                    compositor_id INTEGER REFERENCES compositores(id) ON DELETE SET NULL
                );
            """)
            print("Tabela 'musicas' verificada/atualizada.")

        conn.commit()
    except psycopg2.Error as e:
        print(f"Erro ao inicializar o banco de dados: {e}", file=sys.stderr)
    finally:
        if conn:
            conn.close()

# --- CRUD para Gravadoras ---

def inserir_gravadora(nome):
    """Insere uma nova gravadora."""
    query = "INSERT INTO gravadoras (nome) VALUES (%s);"
    conn = get_conn()
    if not conn: return
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, (nome,))
                flash(f"Gravadora '{nome}' adicionada com sucesso!", 'success')
    except psycopg2.IntegrityError:
        flash(f"Erro: Gravadora '{nome}' já existe.", 'danger')
    except psycopg2.Error as e:
        print(f"Erro ao inserir gravadora: {e}")
    finally:
        conn.close()

def fetch_all_gravadoras():
    """Busca e retorna todas as gravadoras."""
    conn = get_conn()
    if not conn: return []
    gravadoras = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nome FROM gravadoras ORDER BY nome ASC")
            gravadoras = [dict(zip(['id', 'nome'], row)) for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"Erro ao buscar gravadoras: {e}")
    finally:
        conn.close()
    return gravadoras

# --- CRUD para Compositores ---

def inserir_compositor(nome):
    """Insere um novo compositor."""
    query = "INSERT INTO compositores (nome) VALUES (%s);"
    conn = get_conn()
    if not conn: return
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, (nome,))
                flash(f"Compositor '{nome}' adicionado com sucesso!", 'success')
    except psycopg2.IntegrityError:
        flash(f"Erro: Compositor '{nome}' já existe.", 'danger')
    except psycopg2.Error as e:
        print(f"Erro ao inserir compositor: {e}")
    finally:
        conn.close()

def fetch_all_compositores():
    """Busca e retorna todos os compositores."""
    conn = get_conn()
    if not conn: return []
    compositores = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nome FROM compositores ORDER BY nome ASC")
            compositores = [dict(zip(['id', 'nome'], row)) for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"Erro ao buscar compositores: {e}")
    finally:
        conn.close()
    return compositores

# --- CRUD para Músicas (Atualizado) ---

def fetch_all_musicas():
    """Busca e retorna todas as músicas da tabela, incluindo nomes de Gravadora e Compositor."""
    conn = get_conn()
    if not conn: return []
    musicas = []
    query = """
        SELECT 
            m.id, m.titulo, m.artista, m.genero, m.duracao_seconds, m.ano, 
            g.nome AS gravadora_nome, c.nome AS compositor_nome,
            m.gravadora_id, m.compositor_id
        FROM musicas m
        LEFT JOIN gravadoras g ON m.gravadora_id = g.id
        LEFT JOIN compositores c ON m.compositor_id = c.id
        ORDER BY m.id DESC
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            col_names = [desc[0] for desc in cur.description]
            for row in cur.fetchall():
                musicas.append(dict(zip(col_names, row)))
    except psycopg2.Error as e:
        print(f"Erro ao buscar músicas: {e}")
    finally:
        conn.close()
    return musicas

def inserir_musica(titulo, artista, genero, duracao, ano, gravadora_id, compositor_id):
    """Insere uma música no banco de dados, incluindo FKs."""
    query = """
        INSERT INTO musicas (titulo, artista, genero, duracao_seconds, ano, gravadora_id, compositor_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    conn = get_conn()
    if not conn: return
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, (titulo, artista, genero, duracao, ano, gravadora_id, compositor_id))
                flash(f"Música '{titulo}' adicionada com sucesso!", 'success')
    except psycopg2.Error as e:
        print(f"Erro ao inserir música: {e}")
        flash(f"Erro ao inserir música: {e}", 'danger')
    finally:
        conn.close()

def deletar_musica(musica_id):
    """Deleta uma música pelo ID."""
    query = "DELETE FROM musicas WHERE id = %s;"
    conn = get_conn()
    if not conn: return
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, (musica_id,))
                flash("Música deletada com sucesso.", 'info')
    except psycopg2.Error as e:
        print(f"Erro ao deletar música: {e}")
        flash(f"Erro ao deletar música: {e}", 'danger')
    finally:
        conn.close()

# --- ROTAS WEB ---

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Rota principal:
    GET: Visualiza todos os dados e o formulário de adição de música.
    POST: Processa o envio do formulário de música (CREATE).
    """
    if request.method == 'POST':
        # 1. Coleta dados do formulário HTML
        titulo = request.form['titulo']
        artista = request.form['artista']
        genero = request.form['genero']
        
        # Coleta IDs das chaves estrangeiras
        gravadora_id = request.form.get('gravadora_id')
        compositor_id = request.form.get('compositor_id')
        
        # Garante que IDs vazios sejam None para o banco de dados
        gravadora_id = int(gravadora_id) if gravadora_id and gravadora_id.isdigit() else None
        compositor_id = int(compositor_id) if compositor_id and compositor_id.isdigit() else None
        
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
        inserir_musica(titulo, artista, genero, duracao, ano, gravadora_id, compositor_id)
        
        # 3. Redireciona para a mesma página para evitar envio duplicado
        return redirect(url_for('index'))

    # GET: Busca todos os dados para visualização
    musicas = fetch_all_musicas()
    gravadoras = fetch_all_gravadoras()
    compositores = fetch_all_compositores()
    
    return render_template('index.html', 
                           musicas=musicas, 
                           gravadoras=gravadoras,
                           compositores=compositores)

@app.route('/delete/<int:musica_id>', methods=['POST'])
def delete_musica(musica_id):
    """
    Rota para deletar um item específico.
    """
    deletar_musica(musica_id)
    return redirect(url_for('index'))


@app.route('/gravadora/add', methods=['POST'])
def add_gravadora():
    """Rota para adicionar uma nova gravadora."""
    nome = request.form['nome']
    if nome:
        inserir_gravadora(nome)
    return redirect(url_for('index'))

@app.route('/compositor/add', methods=['POST'])
def add_compositor():
    """Rota para adicionar um novo compositor."""
    nome = request.form['nome']
    if nome:
        inserir_compositor(nome)
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Inicializa o banco de dados (cria tabelas se não existirem)
    init_db()
    # Roda a aplicação Flask
    app.run(debug=True)