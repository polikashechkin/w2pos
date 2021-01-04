from sqlalchemy import text as T
from . import Page as BasePage, log

CHECKS_TABLE = 'W2POS#CHECKS'

class Page(BasePage):
    def __init__(self, application, request):
        super().__init__(application, request)

    def __call__(self):
        self.title('Возвращенные чеки')
        sql = f'''
        select 
            c.p_start, c.p_time, c.dept_id, rawtohex(c.ctl_id), c.check_no, c.check_date,
            dept.name, q_fr_smena, q_fr_number, cards, products
        from {CHECKS_TABLE} c, db1_agent dept
        where dept.id = c.dept_id 
        order by p_start desc
        '''
        t = self.Table('checks')
        t.column().text('Дата возврата')
        t.column().text('Дата продажи')
        t.column().text('Подразделение')
        t.column().text('Смена (фр)')
        t.column().text('Чек (фр)')
        t.column().text('Карт')
        t.column().text('Товаров')
        t.column().text('Время (ms)')
        t.column().text('')
        rows = self.oracle.execute(T(sql))
        for p_start, p_time, dept_id, ctl_id, check_no, check_date, dept_name, fr_smena, fr_number, cards, products in rows:
            r = t.row()
            r.text(p_start)
            r.text(str(check_date))
            r.text(f'{dept_name}')
            r.text(fr_smena)
            r.text(fr_number)
            r.text(cards)
            r.text(products)
            r.text(p_time)
            r.href('...', 'pages/check', {'ctl_id':ctl_id, 'check_no':check_no})
    
