class Meal:
    def __init__(self):
        self.burger = None
        self.drink = None
        self.side = None

class MealBuilder:
    def build_burger(self):
        pass

    def build_drink(self):
        pass

    def build_side(self):
        pass

class VegetarianMealBuilder(MealBuilder):
    def build_burger(self):
        # Build a vegetarian burger
        pass

    def build_drink(self):
        # Build a non-alcoholic drink
        pass

    def build_side(self):
        # Build a side dish
        pass

class Director:
    def construct(self, builder):
        builder.build_burger()
        builder.build_drink()
        builder.build_side()
        return builder

# Client code
vegetarian_builder = VegetarianMealBuilder()
director = Director()
meal = director.construct(vegetarian_builder)

