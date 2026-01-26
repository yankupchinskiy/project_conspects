# Механизм RTTI в C++

## Что такое RTTI?

**RTTI (Run-Time Type Information)** — механизм получения информации о типе объекта во время выполнения программы. Это позволяет определять реальный тип объекта, даже если доступ осуществляется через указатель или ссылку на базовый класс.

## Компоненты RTTI

### 1. **Оператор `typeid`**
### 2. **Оператор `dynamic_cast`**
### 3. **Класс `std::type_info`**

## Как работает RTTI?

### Базовый пример
```cpp
#include <iostream>
#include <typeinfo>  // Для typeid

class Base {
public:
    virtual ~Base() {}  // Виртуальный деструктор необходим для RTTI
};

class Derived : public Base {};

int main() {
    Base* basePtr = new Derived();
    
    // Получаем информацию о типе
    const std::type_info& info = typeid(*basePtr);
    std::cout << "Actual type: " << info.name() << std::endl;
    
    delete basePtr;
}
```

## Детали реализации

### 1. **Хранение информации о типе в vtable**
```cpp
// Примерная структура vtable с RTTI
class VTableLayout {
public:
    // 1. Указатели на виртуальные функции
    void (*virtual_func1)(void*);
    void (*virtual_func2)(void*);
    
    // 2. Указатель на type_info (для RTTI)
    const std::type_info* type_info_ptr;
    
    // 3. Дополнительная информация (для dynamic_cast)
    void* base_class_offsets[];
};

// В памяти объект с виртуальными функциями:
// [0] vptr → VTableLayout
// [8+] данные объекта
```

### 2. **Структура `std::type_info`**
```cpp
// Упрощенное представление (фактическая реализация зависит от компилятора)
class type_info {
private:
    const char* name;           // Имя типа (mangled name)
    size_t hash_code;           // Хеш-код типа
    // Дополнительные поля для сравнения типов
public:
    virtual ~type_info();                      // Виртуальный деструктор
    bool operator==(const type_info&) const;   // Сравнение типов
    bool operator!=(const type_info&) const;
    const char* name() const;                  // Получение имени типа
    size_t hash_code() const;                  // Получение хеш-кода
    bool before(const type_info&) const;       // Порядок типов
};
```

## Практическое использование

### 1. **Определение типа с помощью `typeid`**
```cpp
#include <iostream>
#include <typeinfo>
#include <string>

class Animal {
public:
    virtual ~Animal() = default;
};

class Dog : public Animal {};
class Cat : public Animal {};

void identifyAnimal(Animal* animal) {
    const std::type_info& ti = typeid(*animal);
    
    if (ti == typeid(Dog)) {
        std::cout << "It's a Dog" << std::endl;
    } else if (ti == typeid(Cat)) {
        std::cout << "It's a Cat" << std::endl;
    } else if (ti == typeid(Animal)) {
        std::cout << "Just an Animal" << std::endl;
    }
    
    // Получение имени типа (зависит от компилятора)
    std::cout << "Type name: " << ti.name() << std::endl;
    
    // Хеш-код типа (C++11)
    std::cout << "Hash code: " << ti.hash_code() << std::endl;
}

int main() {
    Dog dog;
    Cat cat;
    Animal animal;
    
    identifyAnimal(&dog);    // It's a Dog
    identifyAnimal(&cat);    // It's a Cat
    identifyAnimal(&animal); // Just an Animal
}
```

### 2. **Безопасное приведение типов с `dynamic_cast`**
```cpp
class Shape {
public:
    virtual ~Shape() = default;
    virtual void draw() = 0;
};

class Circle : public Shape {
public:
    void draw() override { std::cout << "Drawing circle" << std::endl; }
    void setRadius(double r) { radius = r; }
private:
    double radius;
};

class Square : public Shape {
public:
    void draw() override { std::cout << "Drawing square" << std::endl; }
    void setSide(double s) { side = s; }
private:
    double side;
};

void processShape(Shape* shape) {
    // Попытка приведения к Circle
    Circle* circle = dynamic_cast<Circle*>(shape);
    if (circle) {
        std::cout << "It's a Circle, setting radius" << std::endl;
        circle->setRadius(5.0);
        return;
    }
    
    // Попытка приведения к Square
    Square* square = dynamic_cast<Square*>(shape);
    if (square) {
        std::cout << "It's a Square, setting side" << std::endl;
        square->setSide(10.0);
        return;
    }
    
    std::cout << "Unknown shape type" << std::endl;
}

int main() {
    Circle circle;
    Square square;
    
    processShape(&circle);  // It's a Circle
    processShape(&square);  // It's a Square
}
```

### 3. **Работа с исключениями в `dynamic_cast`**
```cpp
class Base {
public:
    virtual ~Base() = default;
};

class Derived : public Base {};

void safeCast(Base& ref) {
    try {
        Derived& derived = dynamic_cast<Derived&>(ref);
        std::cout << "Cast successful" << std::endl;
    } catch (const std::bad_cast& e) {
        std::cout << "Bad cast: " << e.what() << std::endl;
    }
}

int main() {
    Base base;
    Derived derived;
    
    safeCast(derived);  // Cast successful
    safeCast(base);     // Bad cast
}
```

## Внутреннее устройство

### Как хранится информация о типах
```cpp
// Примерная реализация компилятором
class Base {
public:
    virtual ~Base() = default;
    
    // Компилятор неявно добавляет:
    // const type_info* __type_info; // в vtable
};

// Для каждого типа создается статический объект type_info
extern "C" const std::type_info type_info_for_Base = {
    "Base",      // mangled name
    0x12345678,  // hash code
    // ... 
};

extern "C" const std::type_info type_info_for_Derived = {
    "Derived",
    0x87654321,
    // ...
};
```

### Пример доступа к RTTI через vtable
```cpp
// Псевдокод: как может выглядеть вызов typeid
const std::type_info& typeid_impl(const void* obj) {
    // Получаем vptr (первое слово в объекте)
    void** vptr = *reinterpret_cast<void***>(const_cast<void*>(obj));
    
    // В vtable есть смещение к type_info
    // Обычно type_info находится после всех виртуальных функций
    const std::type_info* ti = *reinterpret_cast<const std::type_info**>(
        reinterpret_cast<char*>(vptr) + TYPEINFO_OFFSET
    );
    
    return *ti;
}
```

## Ограничения RTTI

### 1. **Требует виртуальных функций**
```cpp
class NonPolymorphic {
    // Нет виртуальных функций
};

int main() {
    NonPolymorphic obj;
    // typeid(obj) работает, но дает статический тип
    // dynamic_cast не применим
}
```

### 2. **Нет информации о типах шаблонов**
```cpp
template<typename T>
class TemplateClass {
    T value;
};

int main() {
    TemplateClass<int> t1;
    TemplateClass<double> t2;
    
    std::cout << typeid(t1).name() << std::endl;  // Разные типы
    std::cout << typeid(t2).name() << std::endl;  // Но RTTI не дает доступ к T
}
```

### 3. **Производительность**
- `typeid`: Одно косвенное обращение к памяти (через vptr)
- `dynamic_cast`: Может требовать обхода иерархии наследования (особенно при множественном наследовании)

## Множественное наследование и RTTI

```cpp
class Base1 {
public:
    virtual ~Base1() = default;
};

class Base2 {
public:
    virtual ~Base2() = default;
};

class Derived : public Base1, public Base2 {};

int main() {
    Derived derived;
    
    Base1* b1 = &derived;
    Base2* b2 = &derived;
    
    // dynamic_cast должен корректировать указатель
    Derived* d1 = dynamic_cast<Derived*>(b1);
    Derived* d2 = dynamic_cast<Derived*>(b2);
    
    // b1 и b2 указывают на разные адреса в объекте
    // но dynamic_cast корректно возвращает указатель на начало объекта
    std::cout << "b1: " << b1 << std::endl;
    std::cout << "b2: " << b2 << std::endl;
    std::cout << "d1: " << d1 << std::endl;
    std::cout << "d2: " << d2 << std::endl;
}
```

## Отключение RTTI

### Компиляторные флаги:
- **GCC/Clang**: `-fno-rtti`
- **MSVC**: `/GR-` (по умолчанию `/GR+`)

### Что происходит при отключении:
```cpp
// С RTTI отключенным этот код не скомпилируется
class Base { virtual ~Base() = default; };
class Derived : public Base {};

int main() {
    Base* b = new Derived();
    
    // Ошибка компиляции: RTTI отключено
    // Derived* d = dynamic_cast<Derived*>(b);
    
    // typeid может работать ограниченно (зависит от реализации)
    // std::cout << typeid(*b).name() << std::endl;
    
    delete b;
}
```

## Альтернативы RTTI

### 1. **Виртуальные функции с определением типа**
```cpp
class Shape {
public:
    enum Type { CIRCLE, SQUARE, TRIANGLE };
    
    virtual Type getType() const = 0;
    virtual ~Shape() = default;
};

class Circle : public Shape {
public:
    Type getType() const override { return CIRCLE; }
    void circleSpecific() {}
};

void process(Shape* shape) {
    switch (shape->getType()) {
        case Shape::CIRCLE:
            static_cast<Circle*>(shape)->circleSpecific();
            break;
        // ...
    }
}
```

### 2. **Использование typeid для статических типов**
```cpp
template<typename T>
void processTemplate() {
    // Информация о типе доступна на этапе компиляции
    std::cout << "Processing type: " << typeid(T).name() << std::endl;
    
    // Можно использовать специализации шаблонов
    if constexpr (std::is_same_v<T, int>) {
        std::cout << "It's an int!" << std::endl;
    }
}
```

## Производительность dynamic_cast

### Сложность операций:
- **Одиночное наследование**: O(1) - проверка типа через type_info
- **Множественное наследование**: O(n) - обход иерархии
- **Виртуальное наследование**: O(n) или хуже

```cpp
// Пример сложной иерархии
class A { virtual ~A() = default; };
class B : virtual public A {};
class C : virtual public A {};
class D : public B, public C {};

void expensiveCast(A* a) {
    // Этот cast может быть дорогим
    D* d = dynamic_cast<D*>(a);
}
```

## Полезные методы type_info

```cpp
#include <iostream>
#include <typeinfo>
#include <vector>

int main() {
    int x = 42;
    double y = 3.14;
    std::vector<int> v;
    
    const std::type_info& ti1 = typeid(x);
    const std::type_info& ti2 = typeid(y);
    const std::type_info& ti3 = typeid(v);
    
    // Сравнение типов
    std::cout << std::boolalpha;
    std::cout << "Same type? " << (ti1 == ti2) << std::endl;  // false
    
    // Порядок типов (определяется реализацией)
    std::cout << "ti1 before ti2? " << ti1.before(ti2) << std::endl;
    
    // Хеш-код для использования в unordered_map
    std::cout << "Hash of int: " << ti1.hash_code() << std::endl;
    
    // Деманглинг имен (зависит от платформы)
    #ifdef __GNUG__
    #include <cxxabi.h>
    char* demangled = abi::__cxa_demangle(ti3.name(), 0, 0, 0);
    std::cout << "Demangled: " << demangled << std::endl;
    free(demangled);
    #endif
}
```

## Best Practices

### ✅ **ХОРОШО:**
```cpp
// 1. Используйте dynamic_cast для безопасного приведения
Base* base = getObject();
if (Derived* derived = dynamic_cast<Derived*>(base)) {
    derived->specificOperation();
}

// 2. Используйте виртуальные функции вместо RTTI когда возможно
class Processor {
public:
    virtual void process() = 0;  // Лучше, чем проверка typeid
};

// 3. Отключайте RTTI в embedded/performance-critical проектах
```

### ❌ **ПЛОХО:**
```cpp
// 1. Избегайте цепочек typeid для определения типа
if (typeid(*obj) == typeid(Type1)) {
    // ...
} else if (typeid(*obj) == typeid(Type2)) {
    // ...
} // Плохо: нарушает OCP

// 2. Не используйте dynamic_cast для downcast в конструкторах/деструкторах
class Base {
public:
    Base() {
        // dynamic_cast не будет работать правильно!
        // Derived* d = dynamic_cast<Derived*>(this);
    }
};

// 3. Не полагайтесь на точный формат name()
std::string typeName = typeid(obj).name();  // Формат зависит от компилятора
```

## Заключение

**RTTI — мощный механизм, который позволяет:**
1. Определять реальный тип объекта во время выполнения
2. Безопасно приводить типы в иерархии наследования
3. Реализовывать полиморфное поведение без явных проверок типа

**Однако он имеет стоимость:**
- Увеличивает размер vtable
- Замедляет выполнение (особенно dynamic_cast)
- Может быть отключен для оптимизации

**Используйте RTTI когда:**
- Нужна безопасная работа с разнородными коллекциями
- Пишете библиотеки общего назначения
- Требуется диагностика или сериализация

**Избегайте когда:**
- Производительность критична
- Работаете с embedded системами
- Можете использовать виртуальные функции или шаблоны