import sys, os, json, sqlite3, arrow, datetime
from sqlalchemy import text as T
from flask import Flask, request
import xml.etree.cElementTree as ET
from domino.core import log
from domino.application import Status
#from domino.databases import Databases
from domino.account import find_account_id

from . import Response as BaseResponse

class Response(BaseResponse):
    def __init__(self, application, request):
        super().__init__(application, request)
        self.oracle = None

    def __call__(self):
        start = datetime.datetime.now()
        #r = Request(request, application)
        account_id = find_account_id(self.get('account_id')) # account_id
        dept_uid = self.get('dept_uid') # UID подразделения 
        date = self.get('date') # дата чека в формате ISO (YYYY-MM-DD HH:MM:SS)
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        fr_uid = self.get('fr_uid') #фискальный регистратор (UID)
        fr_smena = self.get('fr_smena') # фискальный номер смены (Число)
        fr_number = self.get('fr_number') # фискальный номер чека
        self.LOG(f'фр={fr_uid} смена={fr_smena} чек={fr_number} дата={date}')

        BODY = ET.fromstring('<BODY/>')
        ET.SubElement(BODY, 'status').text = 'success'
        CHECK = ET.SubElement(BODY, 'CHECK')

        #Работающие запросы на базе сумок на оракл6
        #1) Поиск чека по 
        #- структурному подразделению 4:0:0:437814 - Самара – МегаСити
        #- дате 04/08/2017
        #- кассовому аппарату 4:10005:0:11 - Kassa-megacity
        #- фискальный номер смены 57
        #- фискальный номер чека 768
        q= '''
        SELECT 
            KL.ID as KL_ID, 
            DOMINO.DominoUIDToString(KL.ID) as KL_UID, 
            TOW_LINE.LINE_NO as CHECK_NO, 
            TOW_LINE.F14286866 as CHECK_DATE,
            KL.DEPARTMENT as DEPT_ID,
            TOW_LINE.F61669377 as GUID,
            TOW_LINE.F14876678 as ORDER_ID,
            DOMINO.DominoUIDToString(TOW_LINE.F28835843) as ORDER_TYPE
        FROM 
            DB1_DOCUMENT KL, DB1_LINE TOW_LINE 
        WHERE 
            KL.DEPARTMENT = DOMINO.StringToDominoUID(:dept_uid) AND 
            KL.CLASS=40304641 AND 
            KL.TYPE=40304641  AND 
            TRUNC(KL.DOC_DATE) >= :D AND 
            TRUNC(KL.PARTN_DATE) <= :D AND 
            KL.PARTNER= DOMINO.StringToDominoUID(:fr_uid) AND 
            KL.PARTN_DOC=:fr_smena AND 
            TOW_LINE.DOCUMENT=KL.ID AND 
            TOW_LINE.TYPE=40304641 AND 
            TOW_LINE.F59375717=:fr_number AND 
            TOW_LINE.CODE<>'02'
        '''
        cur = self.oracle.execute(q, {'D':date, 'dept_uid':dept_uid, 'fr_uid':fr_uid, 'fr_smena': fr_smena, 'fr_number':fr_number})
        r = cur.fetchone()
        if r is None:
            return Status.error(f'Чек не найден').xml()

        KL_ID, KL_UID, CHECK_NO, CHECK_DATE, DEPT_ID, GUID, ORDER_ID, ORDER_TYPE = r

        CHECK.set('DATE', f'{CHECK_DATE}')
        CHECK.set('ID', f'{CHECK_NO}')
        if GUID is not None:
            CHECK.set('GUID', f'{GUID}')
        if ORDER_ID is not None:
            CHECK.set('ORDER_ID', f'{ORDER_ID}')
        if ORDER_TYPE is not None:
            CHECK.set('ORDER_TYPE', f'{ORDER_TYPE}')

        # 2) Отбор товарных строчек найденного чека
        q = T('''
        SELECT 
            DOMINO.DominoUIDToString(TOW_LINE.F59375702) as SALESMAN, 
            TOW_LINE.F14745604 as PODR_CODE,
            DOMINO.DominoUIDToString(TOW_LINE.PRODUCT) as TOW,
            TOW_LINE.F14286857 as TOW_CODE,
            TOW_LINE.F14286852 as KOL,
            TOW_LINE.F15007746 as PRICE_ROZ,
            TOW_LINE.F15007748 as PRICE,
            DOMINO.DominoUIDToString(TOW_LINE.F3342349) as RAZMER,
            TOW_LINE.F6684679 as SER,
            TOW_LINE.F14745605 as RF,
            TOW_LINE.F60424249 as PDF417,
            TOW_LINE.F14680065 as EGAIS,
            TOW_LINE.F60424223 as MARKNO
        FROM 
            DB1_LINE TOW_LINE 
        WHERE 
            TOW_LINE.DOCUMENT = DOMINO.StringToDominoUID(:KL_UID) AND 
            TOW_LINE.LINE_NO = :CHECK_NO AND 
            TOW_LINE.TYPE = 40304641
        ''')
        products = 0
        cur = self.oracle.execute(q, {'KL_UID':KL_UID, 'CHECK_NO':CHECK_NO})
        for SALESMAN, PODR_CODE, TOW, TOW_CODE, KOL, PRICE_ROZ, PRICE, RAZMER, SER, RF, PDF417, EGAIS, MARKNO in cur:
            products += 1
            attrib = {'SALESMAN':f'{SALESMAN}', 'POD_CODE':f'{PODR_CODE}', 'TOW':f'{TOW}', 'TOW_CODE':f'{TOW_CODE}', 'KOL':str(KOL), 'PRICE_ROZ':str(PRICE_ROZ), 'PRICE':str(PRICE), 'mark_code':str(MARKNO) }
            ET.SubElement(CHECK, 'LINE', attrib = attrib)

        # 3) Отбор строк с карточками
        q = T('''
        SELECT 
            DOMINO.DominoUIDToString(CARD_LINE.F14876674) as ID,
            CARD_LINE.CODE as CODE,
            DOMINO.DominoUIDToString(CARD_LINE.F6684673) as CLASS,
            CARD_LINE.F48431141 as NOMINAL,
            CARD_LINE.F14876683 as SUMMA,
            CARD.NAME as NAME_CARD,
            CARD_TYPE.NAME as NAME_TYPE,
            DOMINO.DominoUIDToString(CARD_TYPE.F6684714) as PRIZNAK_TYPE
        FROM 
            DB1_LINE CARD_LINE, DB1_DOCUMENT CARD, DB1_DOCUMENT CARD_TYPE 
        WHERE 
            CARD_LINE.DOCUMENT = DOMINO.StringToDominoUID(:KL_UID)
            AND (CARD_LINE.LINE_NO = :CHECK_NO) 
            AND (CARD_LINE.TYPE = 61669392) 
            AND NOT ( CARD_LINE.F6684673 IN (
                    DOMINO.StringToDominoUID('54919216[59375617]'),
                    DOMINO.StringToDominoUID('54919216[59375618]')
                    )) 
            AND (CARD_LINE.F14876674 = CARD.ID) 
            AND (CARD.PID = CARD_TYPE.ID)
        ''')
        cards = 0
        cur = self.oracle.execute(q, {'CHECK_NO':CHECK_NO, 'KL_UID':KL_UID})
        for ID, CODE, CLASS, NOMINAL, SUMMA, NAME_CARD, NAME_TYPE, PRIZNAK_TYPE in cur:
            cards += 1
            attrib={'ID':f'{ID}', 'CODE':f'{CODE}', 'CLASS':f'{CLASS}', 'SUMMA':str(SUMMA)}
            ET.SubElement(CHECK, 'CARD', attrib = attrib)

        # 4) Записть в таблицу возвращенных чеков
        q= T(f'''
        INSERT INTO W2POS#CHECKS 
        (
            Q_DEPT_UID, Q_DATE, Q_FR_UID, Q_FR_SMENA, Q_FR_NUMBER, 
            DEPT_ID, CTL_ID, CHECK_NO, CHECK_DATE,
            CARDS, PRODUCTS, 
            P_START, P_TIME, PID, THREAD
        )
        values(:0, :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14)
        ''')
        delta = datetime.datetime.now() - start
        delta_ms = delta.total_seconds() * 1000
        #p = [ dept_uid, date, fr_uid, fr_smena, fr_number, \
        #    DEPT_ID, KL_ID, CHECK_NO, CHECK_DATE, cards, products,\
        #    start, delta_ms, os.getpid(), 0 ]
        p = { 
            '0':dept_uid, '1':date, '2':fr_uid, '3':fr_smena, '4':fr_number, \
            '5':DEPT_ID, '6':KL_ID, '7':CHECK_NO, '8':CHECK_DATE, '9':cards, '10':products,\
            '11':start, '12':delta_ms, '13':os.getpid(), '14':0 }
        self.oracle.execute(q, p)
        self.LOG.response_type('xml')
        #return '<?xml version="1.0" encoding="utf-8" ?>' + ET.tostring(BODY, encoding="utf-8").decode('utf-8')
        return ET.tostring(BODY)
