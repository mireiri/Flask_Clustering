from flask import (
    Flask, render_template, request, flash, redirect, url_for,
    send_from_directory
    )
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
from clusterpy import clusterpy


# Flaskの設定
app = Flask(__name__)
key = os.urandom(13)
app.secret_key = key

# データベースの用意
URI = 'sqlite:///file.db'
app.config['SQLALCHEMY_DATABASE_URI'] = URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#モデルの用意
class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=False)
    title = db.Column(db.String(30), unique=False)
    file_path = db.Column(db.String(64), index=True, unique=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now())
    
#データベースの初期化コマンド
@app.cli.command('initdb')
def initialize_DB():
    db.create_all()

# 一覧画面へのアクセス
@app.route('/')
def index():
    header = 'クラスタリングアプリケーション'
    all_data = Data.query.all()
    return render_template('index.html', header=header, all_data=all_data)

# アップロード画面へのアクセス
# アップロード画面から送信される値の受け取り・保存
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        name = request.form['name']
        title = request.form['title']
        file = request.files['file']
        file_path = 'static/' + secure_filename(file.filename)
        file.save(file_path)
        register_data = Data(name=name, title=title, file_path=file_path)
        db.session.add(register_data)
        db.session.commit()
        flash('アップロードに成功しました')
        return redirect(url_for('index'))   
    else:
        header = 'ファイルアップロード'
        return render_template('upload.html', header=header)

# アップロードしたデータとExcelファイルの削除
@app.route('/delete/<int:id>')
def delete(id):
    delete_data = Data.query.get(id)
    delete_file = delete_data.file_path
    db.session.delete(delete_data)
    db.session.commit()
    os.remove(delete_file)
    flash('データを削除しました')
    return redirect(url_for('index'))

# クラスタリングの実行
@app.route('/clustering/<int:id>')   
def clustering(id):
    data = Data.query.get(id)
    file_path = data.file_path
    clusterpy(file_path)
    flash('処理が完了しました')
    return redirect(url_for('index'))   

# ダウンロード・削除画面へのアクセス
@app.route('/dd')
def dd():
    files = os.listdir('download')
    header = 'ダウンロード・削除'
    return render_template('dd.html', header=header, files=files)

# ファイル(PNG/Excel)のダウンロード
@app.route('/download/<string:file>')
def download(file):
    return send_from_directory('download', file, as_attachment=True)

# ファイル(PNG/Excel)の削除
@app.route('/output_delete/<string:file>')
def output_delete(file):
    delete_file_path = 'download/' + file
    os.remove(delete_file_path)
    return redirect(url_for('dd'))


# サーバーの起動（アプリケーションの立ち上げ）
if __name__ == '__main__':
    app.run(debug=True)
    