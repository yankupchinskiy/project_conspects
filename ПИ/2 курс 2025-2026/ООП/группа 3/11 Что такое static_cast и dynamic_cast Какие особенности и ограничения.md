# `static_cast` и `dynamic_cast` в C++

## Общее сравнение

| Характеристика | `static_cast` | `dynamic_cast` |
|----------------|---------------|----------------|
| **Время проверки** | Компиляция | Выполнение |
| **Безопасность** | Нет проверки | Проверка с RTTI |
| **Производительность** | Нулевые накладные расходы | Высокие накладные расходы |
| **Требования** | Логическая совместимость типов | Полиморфные типы (виртуальные функции) |
| **При неудаче** | Неопределенное поведение | Возвращает `nullptr` (для указателей) или исключение (для ссылок) |

## 1. `static_cast` — статическое приведение типов

### Основные возможности

```cpp
#include <iostream>

// 1. Преобразование числовых типов
void numeric_conversions() {
    int i = 42;
    double d = static_cast<double>(i);  // int → double
    float f = 3.14f;
    int j = static_cast<int>(f);       // float → int (3)
    
    char c = 'A';
    int ascii = static_cast<int>(c);   // char → int (65)
}

// 2. Преобразование указателей вверх по иерархии (upcast)
class Base {
public:
    virtual ~Base() = default;
};

class Derived : public Base {};

void pointer_conversions() {
    Derived derived;
    
    // Upcast: Derived* → Base* (безопасно, компилятор знает о наследовании)
    Base* basePtr = static_cast<Base*>(&derived);
    
    // Downcast: Base* → Derived* (опасно, без проверки!)
    Derived* derivedPtr = static_cast<Derived*>(basePtr);
}

// 3. Преобразование к void* и обратно
void void_pointer_conversions() {
    int x = 42;
    void* voidPtr = static_cast<void*>(&x);
    int* intPtr = static_cast<int*>(voidPtr);
    
    std::cout << *intPtr << std::endl;  // 42
}

// 4. Пользовательские преобразования
class MyInt {
    int value;
public:
    explicit MyInt(int v) : value(v) {}
    operator int() const { return value; }  // оператор преобразования
};

void user_defined_conversions() {
    MyInt mi(42);
    int i = static_cast<int>(mi);  // вызывает operator int()
    std::cout << i << std::endl;   // 42
}
```

### Особенности и ограничения

```cpp
class Example {
public:
    void demonstrate_limitations() {
        // 1. НЕ МОЖЕТ удалять const/volatile (используйте const_cast)
        const int ci = 10;
        // int* pi = static_cast<int*>(&ci);  // Ошибка компиляции
        
        // 2. НЕ МОЖЕТ приводить между несвязанными указателями
        int* ip = new int(42);
        // double* dp = static_cast<double*>(ip);  // Ошибка компиляции
        
        // 3. Может выполнять небезопасные преобразования
        Base* base = new Base();
        // Derived* derived = static_cast<Derived*>(base);  // Опасно!
        // derived->someMethod();  // Неопределенное поведение!
    }
};
```

### Безопасные сценарии использования

```cpp
class SafeStaticCast {
public:
    // 1. Enum-class преобразования (C++11)
    enum class Color { RED, GREEN, BLUE };
    enum class TrafficLight { RED, YELLOW, GREEN };
    
    void enum_conversions() {
        Color c = Color::RED;
        int i = static_cast<int>(c);  // 0
        
        // Безопасное преобразование между enum class
        TrafficLight tl = static_cast<TrafficLight>(static_cast<int>(c));
    }
    
    // 2. Преобразование вниз по иерархии с гарантией
    void safe_downcast() {
        Derived derived;
        Base* base = &derived;  // Upcast
        
        // Только если точно знаем, что это Derived
        if (/* гарантия типа */) {
            Derived* derivedPtr = static_cast<Derived*>(base);
        }
    }
};
```

## 2. `dynamic_cast` — динамическое приведение типов

### Основные возможности

```cpp
#include <iostream>
#include <typeinfo>

class Animal {
public:
    virtual ~Animal() = default;  // Виртуальный деструктор ОБЯЗАТЕЛЕН
    virtual void speak() const = 0;
};

class Dog : public Animal {
public:
    void speak() const override {
        std::cout << "Woof!" << std::endl;
    }
    void fetch() {
        std::cout << "Fetching stick..." << std::endl;
    }
};

class Cat : public Animal {
public:
    void speak() const override {
        std::cout << "Meow!" << std::endl;
    }
    void purr() {
        std::cout << "Purring..." << std::endl;
    }
};

void basic_dynamic_cast() {
    Animal* animal = new Dog();
    
    // 1. Безопасное приведение указателя
    Dog* dog = dynamic_cast<Dog*>(animal);
    if (dog) {
        dog->fetch();  // OK: animal действительно был Dog
    } else {
        std::cout << "Not a dog!" << std::endl;
    }
    
    // 2. Попытка приведения к несовместимому типу
    Cat* cat = dynamic_cast<Cat*>(animal);
    if (!cat) {
        std::cout << "Definitely not a cat!" << std::endl;  // Выполнится
    }
    
    delete animal;
}

void reference_dynamic_cast() {
    Dog dog;
    Animal& animalRef = dog;
    
    try {
        // 3. Приведение ссылок (генерирует исключение при неудаче)
        Dog& dogRef = dynamic_cast<Dog&>(animalRef);
        dogRef.fetch();  // OK
    } catch (const std::bad_cast& e) {
        std::cout << "Bad cast: " << e.what() << std::endl;
    }
    
    // 4. Опасное приведение ссылки (выбросит исключение)
    Animal* anotherAnimal = new Cat();
    try {
        Dog& badRef = dynamic_cast<Dog&>(*anotherAnimal);  // std::bad_cast
    } catch (const std::bad_cast& e) {
        std::cout << "Caught bad_cast: " << e.what() << std::endl;
    }
    delete anotherAnimal;
}
```

### Множественное наследование

```cpp
class Flyer {
public:
    virtual ~Flyer() = default;
    virtual void fly() = 0;
};

class Swimmer {
public:
    virtual ~Swimmer() = default;
    virtual void swim() = 0;
};

class Duck : public Animal, public Flyer, public Swimmer {
public:
    void speak() const override {
        std::cout << "Quack!" << std::endl;
    }
    void fly() override {
        std::cout << "Duck flying" << std::endl;
    }
    void swim() override {
        std::cout << "Duck swimming" << std::endl;
    }
};

void multiple_inheritance_cast() {
    Duck duck;
    Animal* animalPtr = &duck;
    
    // Cross-cast: через общий базовый класс
    Swimmer* swimmer = dynamic_cast<Swimmer*>(animalPtr);
    if (swimmer) {
        swimmer->swim();  // OK: Duck является Swimmer
    }
    
    // Приведение к void* и обратно
    void* voidPtr = dynamic_cast<void*>(animalPtr);
    Duck* duckFromVoid = dynamic_cast<Duck*>(static_cast<Animal*>(voidPtr));
}
```

## Сравнительные примеры

### Пример 1: Безопасность

```cpp
class Base {
public:
    virtual ~Base() = default;
    int value = 42;
};

class Derived : public Base {
public:
    int extra = 100;
};

void safety_comparison() {
    Base base;
    Base* basePtr = &base;
    
    // DANGEROUS: static_cast без проверки
    Derived* derivedStatic = static_cast<Derived*>(basePtr);
    if (derivedStatic) {
        std::cout << derivedStatic->extra << std::endl;  // Неопределенное поведение!
        // Читаем мусор из памяти, т.к. Base не имеет поля extra
    }
    
    // SAFE: dynamic_cast с проверкой
    Derived* derivedDynamic = dynamic_cast<Derived*>(basePtr);
    if (derivedDynamic) {
        std::cout << derivedDynamic->extra << std::endl;  // Не выполнится
    } else {
        std::cout << "Safe: Not a Derived object" << std::endl;
    }
}
```

### Пример 2: Производительность

```cpp
#include <chrono>
#include <vector>

class Shape {
public:
    virtual ~Shape() = default;
    virtual double area() const = 0;
};

class Circle : public Shape {
    double radius;
public:
    Circle(double r) : radius(r) {}
    double area() const override { return 3.14159 * radius * radius; }
};

class Square : public Shape {
    double side;
public:
    Square(double s) : side(s) {}
    double area() const override { return side * side; }
};

void performance_test() {
    std::vector<Shape*> shapes;
    
    // Создаем 1 млн объектов
    for (int i = 0; i < 1000000; ++i) {
        if (i % 2 == 0) {
            shapes.push_back(new Circle(i % 10 + 1));
        } else {
            shapes.push_back(new Square(i % 10 + 1));
        }
    }
    
    // Тест static_cast (опасно, но быстро)
    auto start = std::chrono::high_resolution_clock::now();
    for (auto shape : shapes) {
        Circle* circle = static_cast<Circle*>(shape);  // Предполагаем, что все Circle
        // Небезопасно: половина объектов - Square!
    }
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> static_time = end - start;
    
    // Тест dynamic_cast (безопасно, но медленно)
    start = std::chrono::high_resolution_clock::now();
    for (auto shape : shapes) {
        Circle* circle = dynamic_cast<Circle*>(shape);
        if (circle) {
            // Только для реальных Circle
        }
    }
    end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> dynamic_time = end - start;
    
    std::cout << "static_cast: " << static_time.count() << "s\n";
    std::cout << "dynamic_cast: " << dynamic_time.count() << "s\n";
    std::cout << "dynamic_cast slower by: " 
              << dynamic_time.count() / static_time.count() << "x\n";
    
    // Очистка
    for (auto shape : shapes) delete shape;
}
```

## Особые случаи и ограничения

### Ограничения `dynamic_cast`

```cpp
class NonPolymorphicBase {
    // Нет виртуальных функций
};

class NonPolymorphicDerived : public NonPolymorphicBase {};

void limitations() {
    NonPolymorphicBase base;
    NonPolymorphicBase* basePtr = &base;
    
    // 1. НЕ РАБОТАЕТ без виртуальных функций
    // NonPolymorphicDerived* derived = dynamic_cast<NonPolymorphicDerived*>(basePtr);
    // Ошибка компиляции: 'NonPolymorphicBase' is not polymorphic
    
    // 2. НЕ РАБОТАЕТ для встроенных типов
    int x = 42;
    // double* dp = dynamic_cast<double*>(&x);  // Ошибка компиляции
    
    // 3. НЕ МОЖЕТ удалять const (используйте const_cast)
    const Dog constDog;
    const Animal* constAnimal = &constDog;
    // Dog* nonConstDog = dynamic_cast<Dog*>(constAnimal);  // Ошибка компиляции
}
```

### Виртуальное наследование

```cpp
class VirtualBase {
public:
    virtual ~VirtualBase() = default;
    int data = 42;
};

class VirtualDerived1 : virtual public VirtualBase {};
class VirtualDerived2 : virtual public VirtualBase {};
class FinalClass : public VirtualDerived1, public VirtualDerived2 {};

void virtual_inheritance_cast() {
    FinalClass final;
    VirtualDerived1* vd1 = &final;
    
    // dynamic_cast работает с виртуальным наследованием
    VirtualDerived2* vd2 = dynamic_cast<VirtualDerived2*>(vd1);
    if (vd2) {
        std::cout << "Cross-cast successful" << std::endl;
    }
    
    // Приведение к виртуальной базе
    VirtualBase* vb = dynamic_cast<VirtualBase*>(vd1);
}
```

## Best Practices

### ✅ **ПРАВИЛЬНОЕ использование static_cast**

```cpp
// 1. Числовые преобразования с контролем
int safe_numeric_cast(double d) {
    if (d > std::numeric_limits<int>::max() || 
        d < std::numeric_limits<int>::min()) {
        throw std::overflow_error("Value out of range");
    }
    return static_cast<int>(d);  // Теперь безопасно
}

// 2. Upcast в иерархии
void process_base(Base* base) {
    // Всегда безопасно
    Base* baseCopy = static_cast<Base*>(base);
}

// 3. CRTP (Curiously Recurring Template Pattern)
template<typename Derived>
class BaseCRTP {
public:
    Derived& derived() {
        return static_cast<Derived&>(*this);  // Безопасно в CRTP
    }
};
```

### ✅ **ПРАВИЛЬНОЕ использование dynamic_cast**

```cpp
// 1. Проверка типа в гетерогенных коллекциях
void process_animals(const std::vector<Animal*>& animals) {
    for (Animal* animal : animals) {
        if (Dog* dog = dynamic_cast<Dog*>(animal)) {
            dog->fetch();
        } else if (Cat* cat = dynamic_cast<Cat*>(animal)) {
            cat->purr();
        }
    }
}

// 2. Реализация паттерна Visitor без RTTI альтернатив
class Visitor {
public:
    virtual void visit(Dog* dog) = 0;
    virtual void visit(Cat* cat) = 0;
};

class Animal {
public:
    virtual void accept(Visitor& visitor) = 0;
};

class Dog : public Animal {
public:
    void accept(Visitor& visitor) override {
        visitor.visit(this);  // Безопасно, т.к. this - Dog
    }
};

// 3. Безопасное downcast после проверки
void safe_operation(Base* base) {
    if (Derived* derived = dynamic_cast<Derived*>(base)) {
        // Только здесь используем derived-специфичные методы
        derived->specialOperation();
    }
    // Можно продолжать работать с base
}
```

### ❌ **НЕПРАВИЛЬНОЕ использование**

```cpp
// 1. Использование dynamic_cast вместо виртуальных функций
class BadDesign {
public:
    virtual ~BadDesign() = default;
};

class BadDerived : public BadDesign {
public:
    void specific() { /* ... */ }
};

void bad_usage(BadDesign* obj) {
    // ❌ ПЛОХО: используйте виртуальные функции!
    if (BadDerived* derived = dynamic_cast<BadDerived*>(obj)) {
        derived->specific();
    }
}

// 2. Цепочки dynamic_cast
void ugly_code(Animal* animal) {
    if (Dog* dog = dynamic_cast<Dog*>(animal)) {
        // ...
    } else if (Cat* cat = dynamic_cast<Cat*>(animal)) {
        // ...
    } else if (Duck* duck = dynamic_cast<Duck*>(animal)) {
        // ...
    } // ❌ Нарушает OCP (Open/Closed Principle)
}

// 3. Использование static_cast когда нужен dynamic_cast
void dangerous(Base* base) {
    // ❌ ОПАСНО: может быть не Derived
    Derived* derived = static_cast<Derived*>(base);
    derived->riskyMethod();  // Неопределенное поведение!
}
```

## Практические рекомендации

### Когда использовать `static_cast`:
1. **Числовые преобразования** (с проверкой диапазона)
2. **Upcast** в иерархии наследования
3. **Приведения в CRTP**
4. **Преобразования enum class**
5. **Когда тип гарантированно известен** на этапе компиляции

### Когда использовать `dynamic_cast`:
1. **Безопасный downcast** в полиморфной иерархии
2. **Обработка гетерогенных коллекций**
3. **Реализация паттернов типа Visitor**
4. **Когда нужна проверка типа во время выполнения**

### Альтернативы кастам:
```cpp
// Вместо dynamic_cast - виртуальные функции
class Animal {
public:
    virtual void performAction() = 0;  // Каждое животное реализует свою логику
};

// Вместо проверки типа - std::variant (C++17)
using AnimalVariant = std::variant<Dog, Cat, Duck>;
void process_variant(const AnimalVariant& animal) {
    std::visit([](auto&& arg) {
        using T = std::decay_t<decltype(arg)>;
        if constexpr (std::is_same_v<T, Dog>) {
            arg.fetch();
        } else if constexpr (std::is_same_v<T, Cat>) {
            arg.purr();
        }
    }, animal);
}
```

## Таблица принятия решений

| Ситуация | Рекомендация | Пример |
|----------|--------------|---------|
| **Преобразование чисел** | `static_cast` (с проверкой) | `static_cast<int>(double_value)` |
| **Upcast (базовый класс)** | `static_cast` или неявно | `Base* b = static_cast<Base*>(derived)` |
| **Downcast (без гарантии)** | `dynamic_cast` | `if (Derived* d = dynamic_cast<Derived*>(base))` |
| **Downcast (гарантия типа)** | `static_cast` | `static_cast<Derived*>(base)` (только если уверены) |
| **Работа с void*** | `static_cast` | `static_cast<int*>(void_ptr)` |
| **Удаление const** | `const_cast` | `const_cast<T*>(const_ptr)` |
| **Реинтерпретация бит** | `reinterpret_cast` | `reinterpret_cast<uintptr_t>(ptr)` |

## Заключение

**Ключевые выводы:**

1. **`static_cast`** — для преобразований, безопасность которых можно проверить **на этапе компиляции**
2. **`dynamic_cast`** — для безопасных преобразований в полиморфных иерархиях **во время выполнения**
3. **Производительность**: `static_cast` — нулевые накладные расходы, `dynamic_cast` — дорогая операция
4. **Безопасность**: `dynamic_cast` проверяет корректность преобразования, `static_cast` — нет

**Золотое правило:** Используйте минимально необходимый cast. Если можно обойтись без приведения — не приводите. Если можно использовать `static_cast` — не используйте `dynamic_cast`. Если можно использовать виртуальные функции — не используйте касты вообще.