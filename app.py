import os
from flask import Flask, render_template, request, redirect, url_for
from flask_basicauth import BasicAuth
import yfinance as yf

app = Flask(__name__)

# Easy Admin Security (Change username and password as you like)
app.config['BASIC_AUTH_USERNAME'] = 'admin'
app.config['BASIC_AUTH_PASSWORD'] = 'gold1234'  # आप इसे बाद में बदल सकते हैं
basic_auth = BasicAuth(app)

# In-memory database simulation for tracking entries with Double-Lock status
# Status: master_lock (True = Locked, False = Unlocked)
app_state = {
    "master_lock": True,
    "entries": [
        {"id": 1, "date": "2026-06-01", "price": 72500, "qty": "3 Gram", "locked": True},
        {"id": 2, "date": "2026-06-05", "price": 71000, "qty": "3 Gram", "locked": True}
    ]
}

def get_gold_metrics():
    try:
        ticker_gold = yf.Ticker("GC=F")
        ticker_usd = yf.Ticker("INR=X")
        
        gold_data = ticker_gold.history(period="1d")
        usd_data = ticker_usd.history(period="1d")
        
        us_price = gold_data['Close'].iloc[-1]
        usd_rate = usd_data['Close'].iloc[-1]
        
        # 1 Ounce = 31.1035 Grams (US Price to INR Price per Gram)
        inr_per_gram = (us_price * usd_rate) / 31.1035
        accumulation_zone = inr_per_gram * 0.80  # 20% Drop Zone
        
        return {
            "us_price": round(us_price, 2),
            "inr_per_gram": round(inr_per_gram, 2),
            "acc_zone": round(accumulation_zone, 2),
            "sentiment": "BULLISH" if us_price > gold_data['Close'].mean() else "BEARISH"
        }
    except Exception:
        return {"us_price": 0, "inr_per_gram": 0, "acc_zone": 0, "sentiment": "NEUTRAL"}

@app.route('/')
def index():
    data = get_gold_metrics()
    return render_template('index.html', data=data, state=app_state, is_admin=False)

# Admin Panel Route (Protected by Basic Auth - password prompt)
@app.route('/admin', methods=['GET', 'POST'])
@basic_auth.required
def admin_panel():
    data = get_gold_metrics()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'toggle_master':
            app_state['master_lock'] = not app_state['master_lock']
            
        elif action == 'toggle_item':
            item_id = int(request.form.get('item_id'))
            for item in app_state['entries']:
                if item['id'] == item_id:
                    item['locked'] = not item['locked']
                    
        elif action == 'delete_item':
            item_id = int(request.form.get('item_id'))
            # Check Double Lock Condition: Master must be UNLOCKED and Item must be UNLOCKED
            if not app_state['master_lock']:
                app_state['entries'] = [item for item in app_state['entries'] if item['id'] != item_id or item['locked']]
                
        elif action == 'add_entry':
            new_price = float(request.form.get('price', 0))
            new_qty = request.form.get('qty', '1 Gram')
            new_id = len(app_state['entries']) + 1
            app_state['entries'].append({"id": new_id, "date": "Live", "price": new_price, "qty": new_qty, "locked": True})
            
        return redirect(url_for('admin_panel'))
        
    return render_template('index.html', data=data, state=app_state, is_admin=True)

if __name__ == '__main__':
    app.run()
