import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG
import json
import datetime

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
        self.create_tables()
        print("Database connection established")

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
        except Error as e:
            print(f"Error connecting to MySQL Database: {e}")

    def create_tables(self):


        create_team_members = """
        CREATE TABLE IF NOT EXISTS team_members (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            role VARCHAR(100) NOT NULL,
            role_type ENUM('Developer', 'Designer') NOT NULL,
            default_rate DECIMAL(10, 2) NOT NULL,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        create_quotes = """
        CREATE TABLE IF NOT EXISTS quotes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            client_name VARCHAR(100) NOT NULL,
            client_email VARCHAR(100) NOT NULL,
            pages INT NOT NULL,
            complexity VARCHAR(50) NOT NULL,
            timeline INT NOT NULL,
            margin_percentage DECIMAL(5, 2),
            marketing_strategy VARCHAR(100),
            marketing_cost DECIMAL(10, 2),
            base_cost DECIMAL(10, 2),
            total_cost DECIMAL(10, 2) NOT NULL,
            profit DECIMAL(10, 2),
            tech_stack JSON,
            proposal_text TEXT,
            status VARCHAR(20) DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        create_quote_team_members = """
        CREATE TABLE IF NOT EXISTS quote_team_members (
            id INT AUTO_INCREMENT PRIMARY KEY,
            quote_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            role VARCHAR(100) NOT NULL,
            rate DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE
        )
        """

        create_pricing_categories = """
        CREATE TABLE IF NOT EXISTS pricing_components (
        id INT AUTO_INCREMENT PRIMARY KEY,
        component_type VARCHAR(50) NOT NULL,  -- 'tech_stack', 'marketing_strategy', 'complexity'
        name VARCHAR(100) NOT NULL,
        base_price DECIMAL(10, 2) NOT NULL,
        multiplier DECIMAL(5, 2) DEFAULT 1.0,  -- For complexity levels
        description TEXT,
        active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """

        create_pricing_components = """
        CREATE TABLE IF NOT EXISTS pricing_components (
        id INT AUTO_INCREMENT PRIMARY KEY,
        category_id INT NOT NULL,
        name VARCHAR(100) NOT NULL,
        base_price DECIMAL(10, 2) NOT NULL,
        multiplier DECIMAL(5, 2) DEFAULT 1.0,
        description TEXT,
        active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES pricing_categories(id)
        )
        """

        create_monthly_financials = """
        CREATE TABLE IF NOT EXISTS monthly_financials (
        id INT AUTO_INCREMENT PRIMARY KEY,
        month DATE NOT NULL,  -- Store as YYYY-MM-01 for consistent monthly tracking
        revenue DECIMAL(10, 2) NOT NULL DEFAULT 0,
        expenses DECIMAL(10, 2) NOT NULL DEFAULT 0,
        overhead_costs DECIMAL(10, 2) NOT NULL DEFAULT 0,  -- Fixed monthly costs
        profit_loss DECIMAL(10, 2) GENERATED ALWAYS AS (revenue - expenses - overhead_costs) STORED,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
        """

        create_fixed_costs= """
        CREATE TABLE IF NOT EXISTS fixed_costs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        amount DECIMAL(10, 2) NOT NULL,
        frequency ENUM('Monthly', 'Quarterly', 'Annually') NOT NULL,
        description TEXT,
        active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
        """

        create_monthly_revenue = """
        CREATE TABLE IF NOT EXISTS monthly_revenue (
        id INT AUTO_INCREMENT PRIMARY KEY,
        month VARCHAR(9) NOT NULL,
        revenue DECIMAL(10, 2) NOT NULL,
        profit_margin_percentage DECIMAL(5, 2) NOT NULL DEFAULT 50,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        cursor = self.connection.cursor()
        cursor.execute(create_team_members)
        cursor.execute(create_quotes)
        cursor.execute(create_quote_team_members)
        cursor.execute(create_pricing_categories)
        cursor.execute(create_pricing_components)
        cursor.execute(create_monthly_financials)
        cursor.execute(create_fixed_costs)
        cursor.execute(create_monthly_revenue)
        self.connection.commit()
        cursor.close()

    def get_team_members(self, role_type=None):
        cursor = self.connection.cursor(dictionary=True)
        if role_type:
            cursor.execute("SELECT * FROM team_members WHERE role_type = %s AND active = TRUE", (role_type,))
        else:
            cursor.execute("SELECT * FROM team_members WHERE active = TRUE")
        result = cursor.fetchall()
        cursor.close()
        return result

    def add_team_member(self, name, role, role_type, default_rate):
        cursor = self.connection.cursor()
        sql = """
        INSERT INTO team_members (name, role, role_type, default_rate)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (name, role, role_type, default_rate))
        self.connection.commit()
        cursor.close()

    def update_team_member(self, id, name, role, role_type, default_rate):
        cursor = self.connection.cursor()
        sql = """
        UPDATE team_members
        SET name = %s, role = %s, role_type = %s, default_rate = %s
        WHERE id = %s
        """
        cursor.execute(sql, (name, role, role_type, default_rate, id))
        self.connection.commit()
        cursor.close()

    def delete_team_member(self, id):
        try:
            cursor = self.connection.cursor()
            sql = "UPDATE team_members SET active = FALSE WHERE id = %s"
            cursor.execute(sql, (id,))
            self.connection.commit()
        except Error as e:
            print(f"Error deleting team member: {e}")
            self.connection.rollback()
        finally:
            cursor.close()

    def save_quote(self, quote_details):
        """Save quote details to the database"""
        try:
            cursor = self.connection.cursor()
            
            # Insert quote
            quote_sql = """
            INSERT INTO quotes (
                client_name, client_email, pages, complexity, 
                timeline, margin_percentage, marketing_strategy,
                marketing_cost, base_cost, total_cost, profit,
                tech_stack, proposal_text
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(quote_sql, (
                quote_details['client_name'],
                quote_details['client_email'],
                quote_details['pages'],
                quote_details['complexity'],
                quote_details['timeline'],
                quote_details['margin_percentage'],
                quote_details['marketing_strategy'],
                quote_details['marketing_cost'],
                quote_details['base_cost'],
                quote_details['total_cost'],
                quote_details['profit'],
                json.dumps(quote_details['tech_stack']),
                quote_details.get('proposal', '')  # Store the proposal text if available
            ))
            
            quote_id = cursor.lastrowid
            
            # Insert team members for this quote
            team_sql = """
            INSERT INTO quote_team_members (
                quote_id, name, role, rate
            ) VALUES (%s, %s, %s, %s)
            """
            
            for member in quote_details['team_selections']:
                if member['name'] and member['role']:  # Only insert if name and role are present
                    cursor.execute(team_sql, (
                        quote_id,
                        member['name'],
                        member['role'],
                        member['rate']
                    ))
            
            self.connection.commit()
            return quote_id
            
        except Error as e:
            print(f"Error saving quote: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    def get_all_quotes(self):
            """Retrieve all quotes with their team members"""
            try:
                cursor = self.connection.cursor(dictionary=True)
                
                # Get all quotes
                cursor.execute("""
                    SELECT * FROM quotes 
                    ORDER BY created_at DESC
                """)
                quotes = cursor.fetchall()
                
                # For each quote, get its team members
                for quote in quotes:
                    cursor.execute("""
                        SELECT name, role, rate 
                        FROM quote_team_members 
                        WHERE quote_id = %s
                    """, (quote['id'],))
                    quote['team_selections'] = cursor.fetchall()
                    
                    # Convert tech_stack back to list if it exists
                    if quote['tech_stack']:
                        quote['tech_stack'] = json.loads(quote['tech_stack'])
                        
                return quotes
                
            except Error as e:
                print(f"Error retrieving quotes: {e}")
                return []
            finally:
                cursor.close()

    def get_quote(self, quote_id):
        """Retrieve a specific quote with its team members"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Get the quote
            cursor.execute("""
                SELECT * FROM quotes 
                WHERE id = %s
            """, (quote_id,))
            quote = cursor.fetchone()
            
            if quote:
                # Get team members for this quote
                cursor.execute("""
                    SELECT name, role, rate 
                    FROM quote_team_members 
                    WHERE quote_id = %s
                """, (quote_id,))
                quote['team_selections'] = cursor.fetchall()
                
                # Convert tech_stack back to list
                if quote['tech_stack']:
                    quote['tech_stack'] = json.loads(quote['tech_stack'])
                    
            return quote
            
        except Error as e:
            print(f"Error retrieving quote: {e}")
            return None
        finally:
            cursor.close()

    def delete_quote(self, quote_id):
        """Delete a quote and its team members"""
        try:
            cursor = self.connection.cursor()
            
            # Delete the quote (team members will be deleted automatically due to ON DELETE CASCADE)
            cursor.execute("DELETE FROM quotes WHERE id = %s", (quote_id,))
            self.connection.commit()
            return True
            
        except Error as e:
            print(f"Error deleting quote: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()
    
    def update_quote_status(self, quote_id, status):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE quotes 
                SET status = %s 
                WHERE id = %s
            """, (status, quote_id))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error updating quote status: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()

    def save_proposal(self, quote_id, proposal_text, proposal_pdf):
        cursor = self.connection.cursor()
        sql = """
        UPDATE quotes 
        SET proposal = %s, proposal_pdf = %s
        WHERE id = %s
        """
        cursor.execute(sql, (proposal_text, proposal_pdf, quote_id))
        self.connection.commit()
        cursor.close()

    def get_proposal(self, quote_id):
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT proposal, proposal_pdf FROM quotes WHERE id = %s",
            (quote_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        return result

    def get_pricing_categories(self, active_only=True):
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM pricing_categories"
        if active_only:
            query += " WHERE active = TRUE"
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result

    def get_pricing_components(self, category_id=None, active_only=True):
        cursor = self.connection.cursor(dictionary=True)
        query = """
            SELECT pc.*, cat.name as category_name 
            FROM pricing_components pc
            JOIN pricing_categories cat ON pc.category_id = cat.id
            WHERE 1=1
        """
        params = []
        
        if category_id:
            query += " AND pc.category_id = %s"
            params.append(category_id)
        
        if active_only:
            query += " AND pc.active = TRUE"
            
        cursor.execute(query, params)
        result = cursor.fetchall()
        cursor.close()
        return result

    def add_pricing_category(self, name, description=None):
        cursor = self.connection.cursor()
        sql = """
        INSERT INTO pricing_categories (name, description)
        VALUES (%s, %s)
        """
        cursor.execute(sql, (name, description))
        self.connection.commit()
        cursor.close()

    def add_pricing_component(self, category_id, name, base_price, multiplier=1.0, description=None):
        cursor = self.connection.cursor()
        sql = """
        INSERT INTO pricing_components 
        (category_id, name, base_price, multiplier, description)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (category_id, name, base_price, multiplier, description))
        self.connection.commit()
        cursor.close()

    def update_pricing_category(self, id, name, description=None, active=True):
        cursor = self.connection.cursor()
        sql = """
        UPDATE pricing_categories
        SET name = %s, description = %s, active = %s
        WHERE id = %s
        """
        cursor.execute(sql, (name, description, active, id))
        self.connection.commit()
        cursor.close()

    def update_pricing_component(self, id, name, base_price, multiplier=1.0, description=None, active=True):
        cursor = self.connection.cursor()
        sql = """
        UPDATE pricing_components
        SET name = %s, base_price = %s, multiplier = %s, description = %s, active = %s
        WHERE id = %s
        """
        cursor.execute(sql, (name, base_price, multiplier, description, active, id))
        self.connection.commit()
        cursor.close()

    def get_component_price(self, component_name, category_name=None):
        cursor = self.connection.cursor(dictionary=True)
        query = """
            SELECT pc.base_price, pc.multiplier, (pc.base_price * pc.multiplier) as price
            FROM pricing_components pc
            JOIN pricing_categories cat ON pc.category_id = cat.id
            WHERE pc.name = %s AND pc.active = TRUE
        """
        params = [component_name]
        #print("Params: "+params)
        if category_name:
            query += " AND cat.name = %s"
            params.append(category_name)

        #print(query, params)
        cursor.execute(query, params)
        result = cursor.fetchone()
        print(result)
        cursor.close()
        return result if result else {"base_price": 0.0, "multiplier": 1.0, "price": 0.0}

    def save_previous_month_revenue(self, month, revenue, profit_margin_percentage):
        cursor = self.connection.cursor()
        sql = """
        INSERT INTO monthly_revenue (month, revenue, profit_margin_percentage)
        VALUES (%s, %s, %s)
        """
        try:
            cursor.execute(sql, (month, revenue, profit_margin_percentage))
            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error saving previous month's revenue: {e}")
            self.connection.rollback()
            cursor.close()
            return False

    def update_previous_month_revenue(self, month, revenue, profit_margin_percentage):
        cursor = self.connection.cursor()
        sql = """
        UPDATE monthly_revenue
        SET revenue = %s, profit_margin_percentage = %s
        WHERE month = %s
        """
        try:
            cursor.execute(sql, (revenue, profit_margin_percentage, month))
            self.connection.commit()
            cursor.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating previous month's revenue: {e}")
            self.connection.rollback()
            cursor.close()
            return False

    def get_previous_month_revenue(self, month):
        cursor = self.connection.cursor()
        sql = "SELECT profit_margin_percentage FROM monthly_revenue WHERE month = %s ORDER BY month DESC LIMIT 1"
        cursor.execute(sql, (month,))
        result = cursor.fetchone()
        cursor.close()

        if result:
            print(f"Found existing record for month {month}: {result[0]}")
            return result[0]
        else:
            print(f"No existing record found for month {month}")
            return None

    def get_all_previous_month_revenue(self):
        cursor = self.connection.cursor()
        sql = "SELECT month, revenue, profit_margin_percentage FROM monthly_revenue ORDER BY month DESC"
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        return [{"month": row[0], "revenue": row[1], "profit_margin_percentage": row[2]} for row in results]


#The code after this is purely for the handling of the financial predictions and monthly financials analyis
    def add_monthly_financial(self, month, revenue, expenses, overhead_costs, notes=None):
        #"""Add monthly financial data"""
        cursor = self.connection.cursor()
        sql = """
        INSERT INTO monthly_financials (month, revenue, expenses, overhead_costs, notes)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (month, revenue, expenses, overhead_costs, notes))
        self.connection.commit()
        cursor.close()

    def get_monthly_financials(self, start_date=None, end_date=None):
        """Get monthly financial data within date range"""
        cursor = self.connection.cursor(dictionary=True)
        sql = "SELECT * FROM monthly_financials WHERE 1=1"
        params = []
        
        if start_date:
            sql += " AND month >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND month <= %s"
            params.append(end_date)
            
        sql += " ORDER BY month DESC"
        cursor.execute(sql, params)
        result = cursor.fetchall()
        cursor.close()
        return result

    def get_financial_forecast(self, target_month):
        """
        Calculate financial forecast for target month based on:
        1. Previous month's financials
        2. Confirmed projects (Approved status) for target month
        3. Potential projects (Pending status) for target month
        4. Fixed costs
        """
        cursor = self.connection.cursor(dictionary=True)
        
        # Get previous month's financials
        prev_month = (target_month.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        cursor.execute("""
            SELECT * FROM monthly_financials 
            WHERE month = %s
        """, (prev_month,))
        prev_financials = cursor.fetchone() or {
            'revenue': 0,
            'expenses': 0,
            'overhead_costs': 0,
            'profit_loss': 0
        }
        
        # Get confirmed projects revenue for target month
        cursor.execute("""
            SELECT SUM(total_cost) as confirmed_revenue 
            FROM quotes 
            WHERE status = 'Approved' 
            AND MONTH(created_at) = %s 
            AND YEAR(created_at) = %s
        """, (target_month.month, target_month.year))
        confirmed_revenue = cursor.fetchone()['confirmed_revenue'] or 0
        
        # Get potential projects
        cursor.execute("""
            SELECT SUM(total_cost) as potential_revenue 
            FROM quotes 
            WHERE status = 'Pending' 
            AND MONTH(created_at) = %s 
            AND YEAR(created_at) = %s
        """, (target_month.month, target_month.year))
        potential_revenue = cursor.fetchone()['potential_revenue'] or 0
        
        # Get fixed costs
        cursor.execute("""
            SELECT SUM(amount) as fixed_costs 
            FROM fixed_costs 
            WHERE active = TRUE 
            AND frequency = 'Monthly'
        """)
        monthly_fixed_costs = cursor.fetchone()['fixed_costs'] or 0
        
        cursor.close()
        
        # Calculate forecasts
        conservative_forecast = {
            'revenue': confirmed_revenue,
            'expenses': prev_financials['expenses'],
            'overhead_costs': monthly_fixed_costs,
            'profit_loss': confirmed_revenue - prev_financials['expenses'] - monthly_fixed_costs
        }
        
        optimistic_forecast = {
            'revenue': float(confirmed_revenue) + (float(potential_revenue) * 0.7),  # Assuming 70% conversion
            'expenses': prev_financials['expenses'],
            'overhead_costs': monthly_fixed_costs,
            'profit_loss': (confirmed_revenue + (float(potential_revenue) * 0.7)) - prev_financials['expenses'] - monthly_fixed_costs
        }
        
        breakeven_analysis = {
            'current_revenue': confirmed_revenue,
            'needed_revenue': prev_financials['expenses'] + monthly_fixed_costs,
            'revenue_gap': (prev_financials['expenses'] + monthly_fixed_costs) - confirmed_revenue,
            'potential_projects_value': potential_revenue
        }
        
        return {
            'conservative': conservative_forecast,
            'optimistic': optimistic_forecast,
            'breakeven': breakeven_analysis,
            'previous_month': prev_financials
        }