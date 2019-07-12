#------------------------------------------------
from flask import Flask
from flask_restful import Resource, Api
from flask_restful import reqparse
from flaskext.mysql import MySQL
from datetime import datetime
from selenium import webdriver
import time
import gensim
import json
from django.core.serializers.json import DjangoJSONEncoder
from collections import OrderedDict
# import pymysql
# konlpy
from collections import Counter
from konlpy.tag import Twitter

# logging
import logging


app = Flask(__name__)
api = Api(app)

# MySQL 연결
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'manager'
app.config['MYSQL_DATABASE_DB'] = 'bit_project'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
#만들어진 모델 가져오기
model = gensim.models.Word2Vec.load('C:\\Users\\BIT\\Downloads\\ko\\ko.bin')


# 네이버 맞춤법 검사기
def spell_check(content):
    driver = webdriver.Chrome("C:\\Users\\BIT\\Downloads\\chromedriver_win32\\chromedriver.exe")
    driver.get('https://search.naver.com/search.naver?where=nexearch&query=%EB%84%A4%EC%9D%B4%EB%B2%84+%EB%A7%9E%EC%B6%A4%EB%B2%95+%EA%B2%80%EC%82%AC%EA%B8%B0&ie=utf8&sm=tab_she&qdt=0')


    #크롬 드라이버가 켜질 때 까지 기다리는 시간   
    time.sleep(3)

    #검사박스의 input 박스의 Xpath의 값
    element = driver.find_element_by_xpath('''//*[@id="grammar_checker"]/div[2]/div[1]/div/div[1]/textarea''')

    #input 박스에 맞춤법 검사할 사연 넣기
    element.send_keys(content)

    #검사하기 버튼 누르기
    driver.find_element_by_xpath('''//*[@id="grammar_checker"]/div[2]/div[1]/div/div[2]/button''').click()
    
    #로딩시간 기다리기
    time.sleep(3)
    #결과 값 지정
    corrent_content = driver.find_element_by_xpath('''//*[@id="grammar_checker"]/div[2]/div[2]/div/div[1]/p''').text
    print("틀린거",content)
    print("고친거",corrent_content)
    #드라이버 닫기
    driver.close()

    return corrent_content


# 빈도수 분석하여 점수 부여하기
def data_select(result, _topic):
    # 유사도 5개씩과 최대빈도수 5개 배열에 저장(최대 30개)
    print("함수 들어왔습니다!")
    print(result)


    # 각 단어의 벡터화 시킨 유사도 비슷한 5개 단어 넣을 배열
    sim_list = []
    try:
        for k in range(0, 5):
            sim_letter = model.wv.most_similar(result[k])
            sim_list.append(result[k])
            for j in range(0, 5):
                letters = sim_letter[j][0]
                sim_list.append(letters)
    except:
        pass
    print("sim list는", sim_list)
    
    songid_rows = []
    try:
        for i in range(0, len(sim_list)):
            # sql = '''select songid, topic ,fre1, fre2, fre3, fre4, fre5 from song WHERE topic=%s and (concat (FRE1, FRE2, FRE3, FRE4, FRE5) regexp %s)'''
            sql = '''select songid, topic from song where topic = %s and concat (FRE1, FRE2, FRE3, FRE4, FRE5) regexp %s'''
            cursor.execute(sql, (_topic, sim_list[i]))
            rows = cursor.fetchall()

            for row in rows:
                songid_rows.append(row[0])
    except:
        pass

    
        
    songid_rows = list(OrderedDict.fromkeys(songid_rows))
    
    print("1 songid_rows :: ", songid_rows)

    if len(songid_rows) < 3:
        
        sql = '''select songid, topic from song where topic =%s order by like_num desc limit 3'''
        cursor.execute(sql, (_topic))
        rows = cursor.fetchall()

        for row in rows:
            songid_rows.append(row[0])
            
    newRows = []
    
    print("2 songid_rows :: ", songid_rows)

    for i in range(0, len(songid_rows)):
        
        a = songid_rows[i]
        sql = '''select songid, fre1, fre2, fre3, fre4, fre5 from song where songid = %s'''
        cursor.execute(sql, a) 
        b = cursor.fetchone()
        l = list(b)
        l.append(0)
        newRows.append(l)

    print("nenewRows :: ", newRows)
            
    # 사연과 음악 fre 유사도 검사 
    # => 점수매겨서 newRows배열 마지막 인덱스 값에 점수 저장
    for row in newRows:
        for i in range(1, 6):
            for j in range(0, len(sim_list)):
                if row[i] == sim_list[j]:
                    row[-1] += ((6-i) * 5)

    # 사연과 유사곡 3곡 songid get
    newRows.sort(key=lambda x:(x[6],x[0]) , reverse=True)
    print("함수 전 " ,newRows[0], newRows[1], newRows[2])

    return newRows


@app.route('/')
def hello_world():
    return 'Hello World!'

#댓글 지우기
@app.route('/deleteComment', methods=['post'])
def deleteComment():
    try:

        # JSON parameter 
        parser = reqparse.RequestParser()
        parser.add_argument('delete_commentNo', type=int)


        args = parser.parse_args()
        
        _delete_commentNo = args['delete_commentNo']
        
        
        print("삭제할 번호는 ", _delete_commentNo)
        
        sql = '''delete from comment where commentId = %s'''
        cursor.execute(sql, _delete_commentNo)

        cursor.fetchall()
        conn.commit()
        
        return "success"
        
    except Exception as e:
        return {'error': str(e)}


# 게시글 지우기
@app.route('/deletePost', methods=['post'])
def deletePost():
    try:

        # JSON parameter 
        parser = reqparse.RequestParser()
        parser.add_argument('delete_postNo', type=str)
        

        args = parser.parse_args()
        
        delete_postNo = args['delete_postNo']
        
        _delete_postNo = int(delete_postNo)
        print("삭제할 번호는 ", _delete_postNo)
        
        sql = '''delete from story where postNo = %s'''
        cursor.execute(sql, _delete_postNo)

        cursor.fetchall()
        conn.commit()
        
        return "success"
        
    except Exception as e:
        return {'error': str(e)}


# 댓글 입력
@app.route('/writeComment', methods=['post'])
def write_comment():
    try:
        # JSON parameter 
        parser = reqparse.RequestParser()
        
        parser.add_argument('content', type=str)
        parser.add_argument('userId', type=str)
        parser.add_argument('postNo', type=int)

        
        args = parser.parse_args()
        print("여기는 댓글 입력")
        #내부 변수 저장
        _content = args['content']
        _userId = args['userId']
        _postNo = args['postNo']
 
        print(_postNo, _userId, _content)


        # 노래의 fre1~5를 포함하는 행 select query
        sql = '''insert into comment(content, postNo, userId) values(%s, %s, %s)'''
        cursor.execute(sql, (_content, _postNo, _userId))
        
        cursor.fetchall()
        conn.commit()
        
        print("댓글 삽입!")
        return "success"
        
    except Exception as e:
        return {'error': str(e)}



    

# View 부분띄우기
@app.route('/postView', methods=['post','get'])
def viewPostSong():
    try:

        parser = reqparse.RequestParser()
        parser.add_argument('postNo', type=str)
        args = parser.parse_args()
        postNo = args['postNo']
        _postNo = int(postNo)

        sql = '''select songid1, songid2, songid3 from story where postNo = %s'''
        result = cursor.execute(sql, _postNo)

        data = cursor.fetchall()
        
        song_data = []
        comment_data = []
        
        
        # 노래를 리턴할 list에 append
        for i in range(0, 3):
            sql_1 = '''select songId, singer, title, genre from song where songid = %s'''
            cursor.execute(sql_1, data[0][i])
            row_headers=[x[0] for x in cursor.description]
            rows = cursor.fetchall()
    
            for data_1 in rows:
                song_data.append(dict(zip(row_headers, data_1)))
        
        
        
        #댓글 추출
        sql_com = '''select commentId, content, postNo, userId from comment where postNo = %s'''
        cursor.execute(sql_com, postNo)
        data_com = cursor.fetchall()
        row_headers=[x[0] for x in cursor.description] #this will extract row headers


        # 댓글을 리턴할 list에 append
        for result in data_com:
            comment_data.append(dict(zip(row_headers,result)))

        
        json_data = dict(song=song_data, comment=comment_data)


        print(json_data)
        #Json으로 리턴
        return json.dumps(json_data, cls=DjangoJSONEncoder, ensure_ascii=False)
        
    except Exception as e:
        return {'error': str(e)}


# 전체 List를 리턴
@app.route('/allSelect', methods=['get','post'])
def get_all_songs():
    
    sql = '''select * from story'''
    
    # https://stackoverflow.com/questions/43796423/python-converting-mysql-query-result-to-json
    cursor = conn.cursor()
    cursor.execute(sql)
    
    
    data = cursor.fetchall()
    row_headers=[x[0] for x in cursor.description] #this will extract row headers
    json_data = []
    
    for result in data:
        json_data.append(dict(zip(row_headers,result)))
        
    print("success")
    return json.dumps(json_data,cls=DjangoJSONEncoder, ensure_ascii=False)


# 게시글 쓰기
@app.route('/writePost', methods=['post'])
def write_post():
    try:
        # JSON parameter 
        
        parser = reqparse.RequestParser()
        parser.add_argument('title', type=str)
        parser.add_argument('postContent', type=str)
        parser.add_argument('userId', type=str)
        parser.add_argument('topic', type=str)

        
        args = parser.parse_args()
        print("여기는 writepost")
        #내부 변수 저장
        _title = args['title']
        _postContent = args['postContent']
        _userId = args['userId']
        _topic = args['topic']

        correct_spell = spell_check(_postContent)

        #konlpy package
        nlp = Twitter() 
        # nouns = nlp.nouns(_postContent)
        nouns = nlp.nouns(correct_spell)
        count = Counter(nouns)
    
        # 사연의 fre1~5 result 배열에 저장
        result = [] 
        
        # 최대빈도수 다섯개 list에 삽입
        for letter, i in count.most_common(5):
            result.append(str(letter))


        
        print("함수 부릅니다~~~")
        newRows = data_select(result, _topic)
        print("함수 후 " ,newRows[0], newRows[1], newRows[2])

        now = datetime.now()
        print(now)
       

        # #insert into strory query
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = '''insert into story(postContent, regdate ,userid, songid1, songid2, songid3, title, topic) values(%s, %s, %s, %s, %s, %s, %s, %s)'''
        cursor.execute(sql, (correct_spell, now, _userId, newRows[0][0], newRows[1][0], newRows[2][0] ,_title, _topic))
        cursor.fetchall()
        conn.commit()

        return "success"
        
    except Exception as e:
        return {'error': str(e)}


#게시글 업데이트
@app.route('/updatePost', methods=['post'])
def update_post():
    try:
        # JSON parameter 
        parser = reqparse.RequestParser()
        parser.add_argument('title', type=str)
        parser.add_argument('postContent', type=str)
        parser.add_argument('userId', type=str)
        parser.add_argument('postNo', type=int)
        parser.add_argument('topic', type=str)

        args = parser.parse_args()
        print("여기는 업데이트~~~")
        #내부 변수 저장
        _title = args['title']
        _postContent = args['postContent']
        _userId = args['userId']

        _postNo = args['postNo']
        
        print(_postNo)
        _topic = args['topic']
        print("토픽은", _topic)
        
        correct_spell = spell_check(_postContent)


        #konlpy package
        nlp = Twitter() 
        # nouns = nlp.nouns(_postContent)
        nouns = nlp.nouns(correct_spell)
        count = Counter(nouns)
    
        # 사연의 fre1~5 result 배열에 저장
        result = [] 
        # 각 단어의 벡터화 시킨 유사도 비슷한 5개 단어 넣을 배열
        sim_list = []
        
        
        # 최대빈도수 다섯개 list에 삽입
        for letter, i in count.most_common(5):
            result.append(str(letter))


        print("함수 부릅니다~~~")
        newRows = data_select(result, _topic)
        print("함수 후 " ,newRows[0], newRows[1], newRows[2])
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = '''update story set postContent = %s, songid1=%s, songid2=%s, songid3=%s, title=%s, topic=%s where postNo = %s'''
        cursor.execute(sql, (correct_spell, newRows[0][0], newRows[1][0], newRows[2][0] ,_title, _topic, _postNo))
        
        
        cursor.fetchall()
        conn.commit()

        return "success"
        
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    app.run(debug=True)
