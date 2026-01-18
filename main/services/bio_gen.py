import random


def generate_bio():
    age_ranges = [
        (14, 19),
        (20, 29),
        (30, 40),
        (41, 50),
        (51, 60),
        (61, 70),
        (71, 80)
    ]
    weights = [5, 15, 35, 15, 10, 10, 10]

    selected_range = random.choices(age_ranges, weights=weights, k=1)[0]
    age = random.randint(selected_range[0], selected_range[1])

    gender = random.choices(
        population=['Мужчина', 'Женщина', 'Андрогин'],
        weights=[47.5, 47.5, 5],
        k=1
    )[0]

    orientation = random.choices(
        population=[
            'Гетеросексуал',
            'Гомосексуал',
            'Бисексуал',
            'Пансексуал',
            'Асексуал'
        ],
        weights=[50, 20, 20, 5, 5],
        k=1
    )[0]

    return {
        'age': age,
        'gender': gender,
        'orientation': orientation
    }