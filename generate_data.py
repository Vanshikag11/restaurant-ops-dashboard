"""
Generates a synthetic Zomato/Swiggy-style order dataset with realistic,
embedded patterns (city traffic effects, cuisine price tiers, churn,
meal-time peaks) so the downstream SQL/pandas analysis has real signal
to find rather than pure noise.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

N_CUSTOMERS = 2500
N_RESTAURANTS = 180
N_ORDERS = 30000
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 6, 30)

cities = {
    # city: (base_delivery_min, traffic_std, order_share_weight)
    "Mumbai":     (34, 9, 0.22),
    "Bengaluru":  (31, 8, 0.20),
    "Delhi NCR":  (29, 10, 0.20),
    "Pune":       (24, 6, 0.14),
    "Hyderabad":  (26, 7, 0.13),
    "Chennai":    (27, 7, 0.11),
}

cuisines = {
    # cuisine: (avg_order_value, std, popularity_weight)
    "North Indian": (420, 120, 0.22),
    "South Indian": (260, 70, 0.16),
    "Chinese":      (330, 90, 0.15),
    "Fast Food":    (240, 60, 0.18),
    "Biryani":      (380, 100, 0.14),
    "Desserts":     (190, 50, 0.08),
    "Continental":  (560, 150, 0.07),
}

city_names = list(cities.keys())
city_probs = [v[2] for v in cities.values()]
cuisine_names = list(cuisines.keys())
cuisine_probs = [v[2] for v in cuisines.values()]

# --- restaurants ---
restaurant_ids = [f"R{1000+i}" for i in range(N_RESTAURANTS)]
restaurant_city = np.random.choice(city_names, size=N_RESTAURANTS, p=city_probs)
restaurant_cuisine = np.random.choice(cuisine_names, size=N_RESTAURANTS, p=cuisine_probs)
# each restaurant has a small quality/speed skew so some are chronically slow/fast
restaurant_speed_skew = np.random.normal(0, 4, size=N_RESTAURANTS)
restaurants = pd.DataFrame({
    "restaurant_id": restaurant_ids,
    "city": restaurant_city,
    "cuisine": restaurant_cuisine,
    "speed_skew": restaurant_speed_skew,
})

# --- customers ---
customer_ids = [f"C{100000+i}" for i in range(N_CUSTOMERS)]
customer_city = np.random.choice(city_names, size=N_CUSTOMERS, p=city_probs)
# signup date spread over the window, weighted earlier (so churn has something to bite on)
signup_offsets = np.random.exponential(scale=40, size=N_CUSTOMERS).astype(int)
signup_offsets = np.clip(signup_offsets, 0, 150)
customer_signup = [START_DATE + timedelta(days=int(o)) for o in signup_offsets]
customers = pd.DataFrame({
    "customer_id": customer_ids,
    "city": customer_city,
    "signup_date": customer_signup,
})

# --- orders ---
total_days = (END_DATE - START_DATE).days

def random_order_datetime():
    day_offset = np.random.randint(0, total_days)
    date = START_DATE + timedelta(days=day_offset)
    # meal-time peaks: lunch (12-14) and dinner (19-22) weighted heavier
    hour_choices = list(range(8, 24))
    hour_weights = []
    for h in hour_choices:
        if 12 <= h <= 14:
            hour_weights.append(6)
        elif 19 <= h <= 22:
            hour_weights.append(8)
        else:
            hour_weights.append(1)
    hour_weights = np.array(hour_weights, dtype=float)
    hour_weights /= hour_weights.sum()
    hour = np.random.choice(hour_choices, p=hour_weights)
    minute = np.random.randint(0, 60)
    return date.replace(hour=hour, minute=minute)

# weight customers so some are "power users" (repeat) and many are one-and-done (churn-prone)
customer_activity_weight = np.random.pareto(a=1.4, size=N_CUSTOMERS) + 0.2
customer_activity_weight /= customer_activity_weight.sum()

order_customer_idx = np.random.choice(N_CUSTOMERS, size=N_ORDERS, p=customer_activity_weight)
order_restaurant_idx = np.random.randint(0, N_RESTAURANTS, size=N_ORDERS)

rows = []
for i in range(N_ORDERS):
    cust_idx = order_customer_idx[i]
    rest_idx = order_restaurant_idx[i]

    cust = customers.iloc[cust_idx]
    rest = restaurants.iloc[rest_idx]

    order_dt = random_order_datetime()
    if order_dt < cust["signup_date"]:
        order_dt = cust["signup_date"] + timedelta(days=int(np.random.randint(0, 10)))

    city = rest["city"]
    base_time, traffic_std, _ = cities[city]
    weekday = order_dt.weekday()
    is_weekend = weekday >= 5
    hour = order_dt.hour
    is_peak = (12 <= hour <= 14) or (19 <= hour <= 22)

    delivery_time = (
        base_time
        + rest["speed_skew"]
        + (6 if is_peak else 0)
        + (4 if is_weekend else 0)
        + np.random.normal(0, traffic_std)
    )
    delivery_time = max(12, round(delivery_time, 1))

    cuisine = rest["cuisine"]
    aov, aov_std, _ = cuisines[cuisine]
    order_value = max(99, round(np.random.normal(aov, aov_std), 2))

    # rating skews lower when delivery is very slow (realistic coupling)
    base_rating = 4.3 - max(0, (delivery_time - 40) / 40)
    rating = np.clip(np.random.normal(base_rating, 0.4), 1, 5)
    rating = round(rating, 1)

    is_repeat = 1  # placeholder, computed later from full order history

    rows.append({
        "order_id": f"O{200000+i}",
        "customer_id": cust["customer_id"],
        "customer_city": cust["city"],
        "restaurant_id": rest["restaurant_id"],
        "restaurant_city": city,
        "cuisine": cuisine,
        "order_datetime": order_dt,
        "order_value": order_value,
        "delivery_time_mins": delivery_time,
        "rating": rating,
        "is_weekend": is_weekend,
    })

orders = pd.DataFrame(rows).sort_values("order_datetime").reset_index(drop=True)

customers.to_csv("customers.csv", index=False)
restaurants.to_csv("restaurants.csv", index=False)
orders.to_csv("orders.csv", index=False)

print("customers:", customers.shape)
print("restaurants:", restaurants.shape)
print("orders:", orders.shape)
print(orders.head())
