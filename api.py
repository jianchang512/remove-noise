HOST="127.0.0.1"
PORT=5080

import os,time,sys
from pathlib import Path
ROOT_DIR = Path(os.getcwd()).as_posix()
TMPDIR= f'{ROOT_DIR}/tmp'

os.environ['MODELSCOPE_CACHE'] = ROOT_DIR + "/models"
os.environ['HF_HOME'] = ROOT_DIR + "/models"
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = 'true'

Path(ROOT_DIR + "/models").mkdir(parents=True, exist_ok=True)
Path(TMPDIR).mkdir(exist_ok=True)

if sys.platform == 'win32':
    os.environ['PATH'] = f'{ROOT_DIR};{ROOT_DIR}\\ffmpeg;' + os.environ['PATH']
else:
    os.environ['PATH'] = f'{ROOT_DIR}:{ROOT_DIR}/ffmpeg:' + os.environ['PATH']
import re
import torch
from torch.backends import cudnn
import torchaudio
import numpy as np
from flask import Flask, request, jsonify, send_file, render_template,send_from_directory
from flask_cors import CORS


import threading
import soundfile as sf
import io
import tempfile
import logging
import traceback
from waitress import serve




# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')
CORS(app)

@app.route('/tmp/<path:filename>')
def tmp_files(filename):
    return send_from_directory(TMPDIR, filename)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(TMPDIR, filename)


@app.route('/')
def index():
    return render_template("index.html",
       root_dir=ROOT_DIR.replace('\\', '/')
    )

def save_audio(file):
    print(f'{file.filename=}')
    filename=re.sub(r'["\'#\?\>\<\;\,=\+\*~!@\$%\^&\(\)\{\}\|\[\]\s ]+','',file.filename)
    file.save(f'{TMPDIR}/{filename}')
    
    cover_file=f'{Path(filename).stem}-16kconver.wav'
    runffmpeg(['-y','-i',f'{TMPDIR}/{filename}','-ar','16000','-ac','1',f'{TMPDIR}/{cover_file}'])
    file_url = f"{TMPDIR}/{cover_file}" # Replace with your actual URL structure
    return file_url
    
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audio' not in request.files:
        return jsonify({'code': -1, 'msg': '必须选择文件上传'})
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'code': -1, 'msg': '未选择上传文件'})
    file_url=save_audio(file)
    return jsonify({'code': 0, 'data': {'url': file_url}})

@app.route('/api', methods=['GET','POST'])
def denoise():
    data={
        "url":request.form.get('url'),
        "stream":int(request.form.get('stream',0))
    }
    if not data['url'] and not data['stream']:
        data={
            "url":request.args.get('url'),
            "stream":int(request.args.get('stream',0))
        }
    print(f'{data=}')
    processed_url = data.get('url')
    if not processed_url and  'audio' not in request.files:
        return jsonify({'code': -1, 'msg': '必须上传文件或传递音频绝对路径'})
    if not processed_url:
        file=request.files['audio']
        if file.filename == '':
            return jsonify({'code': -1, 'msg': '未选择上传文件'})
        processed_url=save_audio(file)
    
    out_path=processed_url.replace('-16kconver.wav','-remove-noise.wav')
    remove_noise(processed_url,out_path)
    
    if data.get('stream')==1:
        print(f'{out_path=}')
        return send_file(out_path, mimetype="audio/wav",as_attachment=True, download_name='remove-noise.wav')
    
    return jsonify({'code': 0, 'data': {'url': f'http://{HOST}:{PORT}/tmp/'+Path(out_path).name}})


def remove_noise(audio_path, output_file):
    from modelscope.pipelines import pipeline
    from modelscope.utils.constant import Tasks
    try:
        ans = pipeline(
            Tasks.acoustic_noise_suppression,
            model='damo/speech_zipenhancer_ans_multiloss_16k_base')
        result = ans(
            audio_path,
            output_path=output_file)

    except Exception as e:
        logger.exception(e, exc_info=True)
    else:
        return output_file
    return audio_path

def runffmpeg(arg):
    import subprocess
    cmd = ["ffmpeg","-hide_banner","-y"]
    cmd = cmd + arg
    p = subprocess.Popen(cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=0 if sys.platform != 'win32' else subprocess.CREATE_NO_WINDOW)
    while True:
        try:
            #等待0.1未结束则异常
            outs, errs = p.communicate(timeout=0.5)
            errs=str(errs)
            if errs:
                errs = errs.replace('\\\\','\\').replace('\r',' ').replace('\n',' ')
                errs=errs[errs.find("Error"):]
            # 成功
            if p.returncode==0:
                return "ok"
            return errs
        except subprocess.TimeoutExpired as e:
            # 如果前台要求停止
            pass
        except Exception as e:
            #出错异常
            errs=f"[error]ffmpeg:error {cmd=},\n{str(e)}"
            return errs
def openweb(web_address):
    import webbrowser
    try:
        time.sleep(3)
        webbrowser.open(web_address)
        print(f"{web_address}")
    except Exception:
        pass


if __name__ == '__main__':
    try:
        
        print(f"api接口地址  http://{HOST}:{PORT}")
        threading.Thread(target=openweb,args=(f'http://{HOST}:{PORT}',)).start()
        serve(app,host=HOST, port=PORT)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        logger.error(traceback.format_exc())