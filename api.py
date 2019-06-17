from flask import Flask
from flask_restful import Resource, Api
from flask_restful import reqparse
from flaskext.mysql import MySQL
from datetime import datetime

# konlpy
from collections import Counter
from konlpy.tag import Twitter

# logging
import logging


app = Flask(__name__)
api = Api(app)

# MySQL 연결
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'bituser'
app.config['MYSQL_DATABASE_PASSWORD'] = 'bituser'
app.config['MYSQL_DATABASE_DB'] = 'bit_project'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/getSongs')
def get_songs():
    return 'Hello World!'

@app.route('/writeStory', methods=['post'])
def write_story():
    try:
        # JSON parameter 
        parser = reqparse.RequestParser()
        parser.add_argument('title', type=str)
        parser.add_argument('storyContent', type=str)
        parser.add_argument('userId', type=str)

        args = parser.parse_args()

        #내부 변수 저장
        _title = args['title']
        _storyContent = args['storyContent']
        _userId = args['userId']

        # DB 설정
        conn = mysql.connect()
        cursor = conn.cursor()

        #konlpy package
        nlp = Twitter() 
        nouns = nlp.nouns(_storyContent)
        count = Counter(nouns)
    
        # 사연의 fre1~5 result 배열에 저장
        result = [] 
        for letter, i in count.most_common(5):
            result.append(str(letter))

        # 사연의 fre1~5를 포함하는 행 select query
        sql = ' select songid, fre1, fre2, fre3, fre4, fre5 from song WHERE (FRE5 or FRE4 or FRE3 or FRE2 or FRE1) IN (%s, %s, %s, %s, %s)'
        cursor.execute(sql, (result[0],result[1],result[2],result[3],result[4]))
        rows = cursor.fetchall()

        # list 자료형으로 새로 저장
        newRows = []
        for row in rows:
            l = list(row)
            l.append(0)
            newRows.append(l)
        
        # 사연과 음악 fre 유사도 검사 
        # => 점수매겨서 newRows배열 마지막 인덱스 값에 점수 저장
        for row in newRows:
            for i in range(1,6):
                for j in range(0,4):
                    if result[j] == row[i]:
                        row[-1] += ((6-i) * 4)

        # 사연과 유사곡 3곡 songid get
        newRows.sort(key=lambda x:x[6] , reverse=True)

        #insert into strory query
        now = datetime.now()
        sql = 'insert into story(storycontent, regdate ,userid, songid1, songid2, songid3, title) values(%s, %s, %s, %s, %s, %s, %s);'
        cursor.execute(sql, (_storyContent, now, _userId, newRows[0][0], newRows[1][0], newRows[2][0] ,_title))
        cursor.fetchall()
        conn.commit()

        return "success"
        
    except Exception as e:
        return {'error': str(e)}
        
@app.route('/test', methods=['get','post'])
def test():
    try:
        # JSON parameter 
        parser = reqparse.RequestParser()
        #parser.add_argument('storyNo', type=str)
        parser.add_argument('title', type=str)
        #parser.add_argument('topic', type=str)
        parser.add_argument('storyContent', type=str)

        # 추가
        parser.add_argument('userId', type=str)
        



        args = parser.parse_args()

       # _storyNo = args['storyNo']
        _title = args['title']
        _storyContent = args['storyContent']
        #_topic = args['topic']

        # 추가
        _userId = args['userId']
        print("userId :: ", _userId)

        # DB 설정1
        conn = mysql.connect()
        cursor = conn.cursor()

        #story insert query
        now = datetime.now()
        sql = 'insert into story(storycontent, regdate ,userid, title) values(%s, %s, %s, %s);'
        cursor.execute(sql, (_storyContent, now, _userId, _title))
        cursor.fetchall()
        conn.commit()
        

        # 사연 fre1~5 변수 얻기
        nlp = Twitter() 
        nouns = nlp.nouns(_storyContent)
        count = Counter(nouns)
    
        result = [] 

        # 사연 fre1~5 result 배열에 저장
        for letter, i in count.most_common(5):
            result.append(str(letter))
            # logging.warning("type: ", type(letter))
        print("result: ", result)
        

        # logging.warning("hyewon result: ", result, type(result[0]))


        

        # TODO: 노래 추천 알고리즘

        # 사연 fre1~5 가 속한 노래DB 데이터 얻기
        sql = ' select songid, fre1, fre2, fre3, fre4, fre5 from song WHERE (FRE5 or FRE4 or FRE3 or FRE2 or FRE1) IN (%s, %s, %s, %s, %s)'
        cursor.execute(sql, (result[0],result[1],result[2],result[3],result[4]))
        rows = cursor.fetchall()
            
        # logging.warning('rows: ', rows) #logging


        newRows = []


        for row in rows:
            l = list(row)
            l.append(0)
            newRows.append(l)

        # logging.warning(newRows)
       
        for row in newRows:
            for i in range(1,6):
                if result[0] == row[i]:
                    row[-1] += ((6-i) * 4)
                if result[1] == row[i]:
                    row[-1] += ((6-i) * 4)
                if result[2] == row[i]:
                    row[-1] += ((6-i) * 4)
                if result[3] == row[i]:
                    row[-1] += ((6-i) * 4)
                if result[4] == row[i]:
                    row[-1] += ((6-i) * 4)
        # logging.warning("newRows: ", newRows)      

        # 노래 3곡 songid get
        newRows.sort(key=lambda x:x[6] , reverse=True)
          
        for i in range(0,3):
            print("song_id :",newRows[i][0], "score : ", newRows[i][6])
                
        
        # TODO: STORYNO 받기
        
        sql = 'SELECT LAST_INSERT_ID()'
        cursor.execute(sql)
        _storyNo = cursor.fetchall()
        
        print("_storyNo :: ", _storyNo[0][0])


        #업데이트
        # conn = mysql.connect()
        # cursor = conn.cursor()
        sql = 'update story set songid1 = %s, songid2 = %s, songid3 = %s where storyno = %s'
        cursor.execute(sql, (newRows[0][0],newRows[1][0],newRows[2][0], str(_storyNo[0][0])))
        cursorReturn = cursor.fetchall()
        conn.commit()
        

        return "a"
        # return "a"
        # if len(data) is 0:
        #     conn.commit()
        #     return {'StatusCode': '200', 'Message': 'User creation success'}
        # else:
        #     return {'StatusCode': '1000', 'Message': str(data[0])}

    except Exception as e:
        return {'error': str(e)}
# api.add_resource(test, '/test')

if __name__ == '__main__':
    app.run(debug=True)