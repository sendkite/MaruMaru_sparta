from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient

from datetime import datetime, timedelta
import getLating

import jwt  # install PyJWT
import hashlib

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.marumaru

SECRET_KEY = 'BAEMARUMARU'


# 메인페이지 불러오기
@app.route('/')
def main():
    return render_template('index.html')


@app.errorhandler(404)
def page_not():
    return render_template('error.html'), 404


# 게시물목록 페이지 불러오기
@app.route('/list')
def show_posts():
    return render_template('post_list.html')


# 게시물 리스트 불러오기
@app.route('/post_list', methods=['GET'])
def posts_list():
    articles = list(db.articles.find({}, {'_id': False}).sort([("number", -1)]))
    best = db.articles.find_one({}, {'_id': False}, sort=([("view", -1)]))
    return jsonify({'all_articles': articles, 'best': best})


# 이벤트 작성 페이지 불러오기
@app.route('/events')
def show_events():
    return render_template('event_upload.html')


# 이벤트 작성
@app.route('/events', methods=['POST'])
def event_upload():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_information = db.users.find_one({"username": payload["id"]})

    title_receive = request.form['title_give']
    address_receive = request.form['address_give']
    contents_receive = request.form['content_give']
    date_receive = request.form['date_give']
    present_date_receive = request.form['present_date_give']
    max_receive = request.form['max_give']

    file = request.files['file_give']

    extension = file.filename.split('.')

    today = datetime.now()
    mytime = today.strftime('%Y년%m월%d일%H:%M:%S')

    filename = f'{mytime}-{extension[0]}'
    filename = "".join(i for i in filename if i not in "\/:*?<>|")
    filename = filename.strip()

    save_to = f'static/eventimg/{filename}.{extension[1]}'

    file.save(save_to)

    count = db.events.count()
    if count == 0:
        max_value = 1
    else:
        max_value = db.events.find_one(sort=[("idx", -1)])['idx'] + 1

    doc = {
        'idx': max_value,
        'username': user_information["username"],
        'profile_name': user_information["profile_name"],
        'title': title_receive,
        'contents': contents_receive,
        'address': address_receive,
        'file': f'{filename}.{extension[1]}',
        'date': date_receive,
        'present_date': present_date_receive,
        'max': max_receive,
        'comment': list()
    }

    db.events.insert_one(doc)
    return jsonify({'msg': '저장 완료!'})


# 이벤트 목록 페이지 불러오기
@app.route('/event/list')
def show_events_list():
    return render_template('event_list.html')


# 이벤트 리스트 불러오기
@app.route('/events/list', methods=['GET'])
def event_list():
    events = list(db.events.find({}, {'_id': False}))
    return jsonify({'result': 'success', 'all_events': events})


# 이벤트디테일 페이지 불러오기
@app.route('/event/detail/<id>', methods=['GET'])
def event_detail(id):
    db.events.update_one({'idx': int(id)}, {'$inc': {'view': 1}})
    events = db.events.find_one({'idx': int(id)}, {'_id': False})
    print(events)
    if events:
        return render_template("event_detail.html", id=id, events_db=events)
    else:
        return render_template("error.html")


# 이벤트 삭제 api
@app.route('/event/detail', methods=['DELETE'])
def event_delete():
    id_receive = request.form['id_give']
    db.challenge.delete_one({'idx': int(id_receive)})
    return jsonify({'result': 'success', 'msg': '챌린지 삭제 되었습니다.'})


# 이벤트 디테일 수정 화면 GET
@app.route('/pre-eventDetail/<id>/', methods=['GET'])
def event_detail_upload(id):
    events = db.events.find_one({'idx': int(id)}, {'_id': False})
    return render_template("event_detail_upload.html", events=events, id=id)


# 이벤트 디테일 수정 api
@app.route('/event/detail', methods=['PUT'])
def event_detail_post_upload():
    id_receive = request.form['id_give']
    title_receive = request.form['title_give']
    address_receive = request.form['address_give']
    contents_receive = request.form['contents_give']
    date_receive = request.form['date_give']
    max_receive = request.form['max_give']
    db.events.update_one({'idx': int(id_receive)},
                           {'$set': {'title': title_receive, 'contents': contents_receive, 'address': address_receive,
                                     'date': date_receive, 'max': max_receive}})
    return jsonify({'result': 'success', 'msg': '게시물을 수정합니다!'})


# 메인페이지에 프로필 카드 보여주기
@app.route('/profile_list', methods=['GET'])
def show_profile():
    profiles = list(db.profile.find({}, {'_id': False}))
    return jsonify({'all_profile': profiles})


# 지도 맵핑
@app.route('/map', methods=['GET'])
def mapping():
    id = request.args["id"]
    address = db.articles.find_one({'number': int(id)}, {'_id': False})['address']
    address_coor = getLating.getLatLng(address)
    return render_template('locate_map.html', lat=address_coor[0], lon=address_coor[1])


# 디테일 페이지 불러오기
@app.route('/detail/<id>', methods=['GET'])
def detail(id):
    db.articles.update_one({'number': int(id)}, {'$inc': {'view': 1}})
    articles = db.articles.find_one({'number': int(id)}, {'_id': False})
    if articles:
        return render_template("detail.html", id=id, detail_db=articles)
    else:
        return render_template("error.html")


# 디테일 수정 화면 GET
@app.route('/per-detail/<id>/', methods=['GET'])
def detail_upload(id):
    post = db.articles.find_one({'number': int(id)}, {'_id': False})
    return render_template("detail_upload.html", post=post, id=id)


# 디테일 수정 api
@app.route('/detail', methods=['PUT'])
def detail_post_upload():
    id_receive = request.form["id_give"]
    title_receive = request.form["title_give"]
    contents_receive = request.form["contents_give"]

    db.articles.update_one({'number': int(id_receive)},
                           {'$set': {'title': title_receive, 'contents': contents_receive}})
    return jsonify({'result': 'success', 'msg': '게시물을 수정합니다!'})


# 디테일 삭제 api
@app.route('/detail', methods=['DELETE'])
def post_delete():
    id_receive = request.form["id_give"]
    db.articles.delete_one({'number': int(id_receive)})
    return jsonify({'result': 'success', 'msg': '게시글 삭제'})


# 게시물 작성페이지 불러오기
@app.route('/posts')
def show_posts_upload():
    return render_template('post_upload.html')


# 게시물 작성
@app.route('/posts', methods=['POST'])
def post_upload():
    author_receive = request.form['author_give']
    title_receive = request.form['title_give']
    address_receive = request.form['address_give']
    contents_receive = request.form['content_give']
    filename_receive = request.form['filename_give']

    file = request.files['file_give']

    extension = file.filename.split('.')

    today = datetime.now()
    mytime = today.strftime('%Y년%m월%d일%H:%M:%S')

    filename = f'{mytime}-{extension[0]}'

    filename = "".join(i for i in filename if i not in "\/:*?<>|")

    filename = filename.strip()
    save_to = f'static/postimg/{filename}.{extension[1]}'
    file.save(save_to)

    count = db.articles.count()
    # 게시글 삭제시 중복 가능 ->   존재하는  number +1 로 바꿔야함
    if count == 0:
        max_value = 1
    else:
        max_value = db.articles.find_one(sort=[("number", -1)])['number'] + 1

    doc = {
        'author': author_receive,
        'title': title_receive,
        'contents': contents_receive,
        'address': address_receive,
        'number': max_value,
        'file': f'{filename}.{extension[1]}',
        'present_time': mytime,
        'comment': list(),
        'view': 0
    }

    db.articles.insert_one(doc)
    return jsonify({'msg': '저장 완료!'})


# 댓글 작성
@app.route('/comment', methods=['POST'])
def comment_upload():
    id_receive = request.form["id_give"]
    comment = request.form["comment_give"]

    doc = {"comment": comment, "user": "오지조"}
    db.articles.update_one({'number': int(id_receive)}, {"$addToSet": {"comment": doc}})
    save_comment = db.articles.find_one({'number': int(id_receive)}, {'_id': False})
    return jsonify({'msg': '댓글 저장!', 'save_comment': save_comment})


# 프로필 작성 페이지 불러오기
@app.route('/profile/create')
def show_profile_upload():
    return render_template('profile_upload.html')


# 프로필 작성
@app.route('/profile/create', methods=['POST'])
def profile_upload():
    name_receive = request.form["name_give"]
    age_receive = request.form["age_give"]
    gender_receive = request.form["gender_give"]
    comment_receive = request.form["comment_give"]

    file = request.files['file_give']

    extension = file.filename.split('.')

    today = datetime.now()
    mytime = today.strftime('%Y년%m월%d일%H:%M:%S')

    filename = f'{mytime}-{extension[0]}'

    filename = "".join(i for i in filename if i not in "\/:*?<>|")

    filename = filename.strip()
    save_to = f'static/profileimg/{filename}.{extension[1]}'
    file.save(save_to)

    count = db.profile.count()
    # 게시글 삭제시 중복 가능 ->   존재하는  number +1 로 바꿔야함
    if count == 0:
        count = 1
    elif count > 0:
        count = count + 1

    doc = {
        'name': name_receive,
        'age': age_receive,
        'gender': gender_receive,
        'comment': comment_receive,
        'number': count,
        'file': f'{filename}.{extension[1]}'
    }

    db.profile.insert_one(doc)
    return jsonify({'msg': '저장 완료!'})


# 프로필 목록 불러오기
@app.route('/profiles')
def show_profile_list():
    return render_template('profile_list.html')


@app.route('/dogprofile/list', methods=['GET'])
def dogprofile_list():
    profiles = list(db.profile.find({}, {'_id': False}))
    return jsonify({'all_profile': profiles})


# 프로필 상세 페이지 불러오기
@app.route('/profile/<id>', methods=['GET'])
def profile_detail(id):
    profiles = db.profile.find_one({'number': int(id)}, {'_id': False})
    return render_template("profile_detail.html", id=id, detail_db=profiles)


@app.route('/login', methods=['GET'])
def login():
    # 로그인 버튼 클릭시 - 쿠키에 값 있으면, 바로 로그인 추가

    return render_template('login.html')


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    # 중복확인
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        "profile_name": username_receive,  # 프로필 이름 기본값은 아이디
        "profile_pic": "profile_pics/profile_placeholder.png",  # 프로필 사진 파일 이름(기본이미지)
        "profile_info": "",  # 프로필 한 마디
        "baby": list()  # 아가들 리스트
    }
    db.users.insert_one(doc)

    payload = {
        'id': username_receive,
        'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 4)  # 로그인 4시간 유지
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    return jsonify({'result': 'success', 'token': token})


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 4)  # 로그인 4시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/user_info', methods=['GET'])
def user_info():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_information = db.users.find_one({"username": payload["id"]}, {'_id': False})
        return jsonify({'result': 'success', 'user_info': user_information})

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))


@app.route('/user_profile', methods=['GET', 'POST'])
def user_profile():
    token_receive = request.cookies.get('mytoken')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_information = db.users.find_one({"username": payload["id"]}, {'_id': False})

    if (request.method == 'GET'):
        return render_template('user_profile_upload.html', user_info=user_information)

    elif (request.method == 'POST'):
        return render_template('user_profile.html', user_info=user_information)


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
