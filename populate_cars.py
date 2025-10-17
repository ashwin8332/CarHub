from app import app, db, Car

# Sample car data based on the cars.html template
cars_data = [
    {
        'name': 'Bugatti Centodieci',
        'slug': 'bugatti-centodieci',
        'price': 9000000,
        'category': 'hypercar',
        'description': 'A rare hypercar with stunning performance and design. Limited edition.',
        'video_url': '/static/bugatti_centodieci.mp4'
    },
    {
        'name': 'McLaren 720S',
        'slug': 'mclaren-720s',
        'price': 300000,
        'category': 'sports',
        'description': 'British supercar with exceptional performance and luxury.',
        'video_url': '/static/McLaren.mp4'
    },
    {
        'name': 'Maruti Suzuki XL6',
        'slug': 'maruti-suzuki-xl6',
        'price': 12000,
        'category': 'family',
        'description': 'Premium multi-purpose vehicle for Indian families.',
        'video_url': '/static/McLaren.mp4'
    },
    {
        'name': 'Bentley Mulliner Batur',
        'slug': 'bentley-mulliner-batur',
        'price': 2000000,
        'category': 'luxury',
        'description': 'Ultra-luxury grand tourer with bespoke craftsmanship.',
        'video_url': '/static/McLaren.mp4'
    },
    {
        'name': 'Lamborghini Diablo SV',
        'slug': 'lamborghini-diablo-sv',
        'price': 500000,
        'category': 'classic sports',
        'description': 'Iconic 90s supercar with legendary V12 engine.',
        'video_url': '/static/1995_lamborghini_diablo_sv.glb'
    },
    {
        'name': 'Tesla Model 3',
        'slug': 'tesla-model-3',
        'price': 40000,
        'category': 'electric',
        'description': 'Popular electric sedan with advanced technology.',
        'video_url': '/static/tesla_m3_model.glb'
    },
    {
        'name': 'Tesla Cybertruck',
        'slug': 'tesla-cybertruck',
        'price': 100000,
        'category': 'electric truck',
        'description': 'Revolutionary electric pickup truck with unique design.',
        'video_url': '/static/tesla_cybertruck.glb'
    },
    {
        'name': 'Tata Tiago',
        'slug': 'tata-tiago',
        'price': 8000,
        'category': 'hatchback',
        'description': 'A reliable and affordable family hatchback with modern features.',
        'video_url': '/static/tata_tiago.glb'
    },
    {
        'name': 'Rolls Royce Spectre',
        'slug': 'rolls-royce-spectre',
        'price': 1200000,
        'category': 'luxury',
        'description': 'The pinnacle of luxury electric grand touring.',
        'video_url': '/static/rolls-royce_spectre.glb'
    },
    {
        'name': 'Rolls Royce Ghost',
        'slug': 'rolls-royce-ghost',
        'price': 350000,
        'category': 'luxury',
        'description': 'The most luxurious sedan with whisper-quiet ride.',
        'video_url': '/static/rolls_royce_ghost.glb'
    },
    {
        'name': 'Porsche 718 Cayman GT4',
        'slug': 'porsche-718-cayman-gt4',
        'price': 85000,
        'category': 'sports',
        'description': 'Perfect balance of performance and daily usability.',
        'video_url': '/static/porsche_718_cayman_gt4.glb'
    },
    {
        'name': 'Mercedes Maybach',
        'slug': 'mercedes-maybach',
        'price': 200000,
        'category': 'luxury',
        'description': 'Ultimate luxury sedan with exceptional comfort.',
        'video_url': '/static/mercedes-benz_maybach_2022.glb'
    },
    {
        'name': 'Lamborghini Revuelto',
        'slug': 'lamborghini-revuelto',
        'price': 608000,
        'category': 'hypercar',
        'description': 'First hybrid V12 Lamborghini with incredible performance.',
        'video_url': '/static/lamborghini_revuelto.glb'
    },
    {
        'name': 'Ferrari Monza SP1',
        'slug': 'ferrari-monza-sp1',
        'price': 1750000,
        'category': 'limited edition',
        'description': 'Exclusive single-seater speedster with racing DNA.',
        'video_url': '/static/ferrari_monza_sp1.glb'
    },
    {
        'name': 'BMW M2 G87',
        'slug': 'bmw-m2-g87',
        'price': 65000,
        'category': 'sports',
        'description': 'Compact sports coupe with M performance DNA.',
        'video_url': '/static/bmw_m2_g87.glb'
    },
    {
        'name': 'Aston Martin V8 Vantage',
        'slug': 'aston-martin-v8-vantage',
        'price': 150000,
        'category': 'grand tourer',
        'description': 'British grand tourer with stunning design and performance.',
        'video_url': '/static/aston_martin_v8_vantage.glb'
    },
    {
        'name': 'Lamborghini Temerario',
        'slug': 'lamborghini-temerario',
        'price': 520000,
        'category': 'sports',
        'description': 'Latest hybrid V8 Lamborghini with cutting-edge technology.',
        'video_url': '/static/lamborghini_temerario.glb'
    },
    {
        'name': 'Hyundai Ioniq 5N',
        'slug': 'hyundai-ioniq-5n',
        'price': 67000,
        'category': 'electric sports',
        'description': 'High-performance electric SUV with track capabilities.',
        'video_url': '/static/2024_hyundai_ioniq_5_n.glb'
    },
    {
        'name': 'Jeep Wrangler Rubicon',
        'slug': 'jeep-wrangler-rubicon',
        'price': 45000,
        'category': 'off-road',
        'description': 'Ultimate off-road SUV with legendary capability.',
        'video_url': '/static/jeep_wrangler_rubicon.glb'
    },
    {
        'name': 'Mahindra Scorpio',
        'slug': 'mahindra-scorpio',
        'price': 15000,
        'category': 'suv',
        'description': 'Rugged SUV with commanding presence and reliable performance.',
        'video_url': '/static/mahindra_scorpio.glb'
    }
]

def populate_database():
    with app.app_context():
        # Clear existing cars (optional)
        Car.query.delete()
        
        # Add cars to database
        for car_data in cars_data:
            car = Car(
                name=car_data['name'],
                slug=car_data['slug'],
                price=car_data['price'],
                category=car_data['category'],
                description=car_data['description'],
                video_url=car_data['video_url']
            )
            db.session.add(car)
        
        db.session.commit()
        print(f"Successfully added {len(cars_data)} cars to the database!")

if __name__ == '__main__':
    populate_database()
