from sqlalchemy import text as T, bindparam
from . import Page as BasePage, log

CHECKS_TABLE = 'W2POS#CHECKS'

class Page(BasePage):
    def __init__(self, application, request):
        super().__init__(application, request)

    def __call__(self):
        #page.application['navbar'](page)
        self.title('Чек')
        ctl_id = self.get('ctl_id')
        check_no = self.get('check_no')
        #account_id = self.account_id
        #cur = self.db_connection.cursor()

        #about_check = self.text_block('about_check')
        check_params = self.Table('check_params')
        sql = T(f'''
        select 
            c.p_start, c.p_time, c.dept_id, c.check_date,
            dept.name, q_fr_smena, q_fr_number, cards, products
        from 
            {CHECKS_TABLE} c, db1_agent dept
        where 
            c.ctl_id=:ctl_id and c.check_no= :check_no and dept.id = c.dept_id 
        ''').bindparams(bindparam('ctl_id', ctl_id), bindparam('check_no',check_no))
        
        #, [ctl_id, check_no])
        row = self.oracle.execute(sql).fetchone()
        p_start, p_time, dept_id, check_date, dept_name, fr_smena, fr_number, crds, products = row
        check_params.row().fields('UID смены (домино)',f'{ctl_id}')
        check_params.row().fields('Номер чека (домино)',f'{check_no}')
        check_params.row().fields('Подразделение',f'{dept_name}')

        #about_cards = self.text_block('about_cards')
        #cards = self.Table('cards')

        #about_products = self.text_block('about_products')
        #cards = self.table('cards')

    