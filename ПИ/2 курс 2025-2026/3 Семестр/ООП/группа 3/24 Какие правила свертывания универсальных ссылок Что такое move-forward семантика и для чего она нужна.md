# Правила свёртывания ссылок (Reference Collapsing) в C++

## Основные правила

Правила свёртывания ссылок применяются, когда в процессе вывода типа или инстанцирования шаблона образуется "ссылка на ссылку". В C++ напрямую нельзя объявить ссылку на ссылку, но это может возникнуть при:

1. Выводе типов в шаблонах
2. Использовании typedef/alias templates
3. Автоматическом выводе типов (auto/decltype)

### **Четыре правила свёртывания**:

| Тип 1 | Тип 2 | Результат свёртывания |
|-------|-------|----------------------|
| `T&`  | `&`   | `T&` (lvalue-ссылка) |
| `T&`  | `&&`  | `T&` (lvalue-ссылка) |
| `T&&` | `&`   | `T&` (lvalue-ссылка) |
| `T&&` | `&&`  | `T&&` (rvalue-ссылка) |

**Проще запомнить**: Если хотя бы одна из ссылок - lvalue-ссылка (`&`), результат будет lvalue-ссылкой. Только если обе - rvalue-ссылки (`&&`), результат будет rvalue-ссылкой.

## Детальные примеры

### 1. **В шаблонных функциях с универсальными ссылками**

```cpp
template<typename T>
void func(T&& param) {
    // param будет свёрнут в зависимости от переданного аргумента
}

int x = 10;
func(x);   // T = int&,  T&& = int& && → int& (lvalue)
func(10);  // T = int,   T&& = int && → int&& (rvalue)
```

### 2. **При использовании typedef/using**

```cpp
typedef int&  lref;
typedef int&& rref;

int n = 10;

lref&  r1 = n;   // int& &  → int&
lref&& r2 = n;   // int& && → int&
rref&  r3 = n;   // int&& & → int&
rref&& r4 = 10;  // int&& && → int&&
```

### 3. **С decltype и auto**

```cpp
int x = 10;
int& y = x;

auto&& z1 = x;    // auto = int&, auto&& = int& && → int&
auto&& z2 = y;    // auto = int&, auto&& = int& && → int&
auto&& z3 = 10;   // auto = int, auto&& = int&& → int&&

decltype(x)&& d1 = std::move(x);  // int&& && → int&&
decltype(y)&& d2 = std::move(x);  // int& && → int& (Ошибка! Невозможно инициализировать int& rvalue)
```

### 4. **В шаблонных классах**

```cpp
template<typename T>
struct ReferenceWrapper {
    using lref_type = T&;
    using rref_type = T&&;
    
    using collapsed_lref = lref_type&;   // T& & → T&
    using collapsed_rref = rref_type&&;  // T&& && → T&&
};
```

## Практическое применение в perfect forwarding

```cpp
#include <utility>

template<typename T>
void forwarder(T&& arg) {
    // Без свёртывания ссылок это бы не работало:
    // Для lvalue: T = int&, тогда T&& = int& && = int&
    // Для rvalue: T = int, тогда T&& = int&&
    target(std::forward<T>(arg));
}

void target(int&);   // Ожидает lvalue
void target(int&&);  // Ожидает rvalue

int main() {
    int x = 5;
    forwarder(x);        // Вызывает target(int&)
    forwarder(10);       // Вызывает target(int&&)
    forwarder(std::move(x)); // Вызывает target(int&&)
}
```

# Move-Forward семантика в C++

## Move семантика

### **Зачем нужна move семантика?**
Для эффективного переноса ресурсов из временных объектов без дорогостоящего копирования.

### **Основные компоненты**:

```cpp
class ResourceHolder {
    int* data;
    size_t size;
    
public:
    // 1. Конструктор перемещения
    ResourceHolder(ResourceHolder&& other) noexcept
        : data(other.data), size(other.size) {
        other.data = nullptr;  // "Обнуляем" у источника
        other.size = 0;
    }
    
    // 2. Оператор присваивания перемещением
    ResourceHolder& operator=(ResourceHolder&& other) noexcept {
        if (this != &other) {
            delete[] data;      // Освобождаем текущие ресурсы
            
            data = other.data;  // Забираем ресурсы
            size = other.size;
            
            other.data = nullptr;
            other.size = 0;
        }
        return *this;
    }
    
    // 3. Деструктор
    ~ResourceHolder() {
        delete[] data;
    }
};
```

### **std::move - каст к rvalue**

```cpp
#include <utility>

std::vector<int> create_vector() {
    return std::vector<int>{1, 2, 3};  // RVO может убрать копирование
}

int main() {
    std::vector<int> v1{1, 2, 3};
    
    // Копирование (дорого для больших векторов)
    std::vector<int> v2 = v1;  
    
    // Перемещение (дешево - просто перенос указателей)
    std::vector<int> v3 = std::move(v1);
    
    // v1 теперь в валидном, но неопределенном состоянии
    // Обычно пустой, но можно присвоить новое значение
    v1 = {4, 5, 6};  // OK
}
```

## Forward семантика (Perfect Forwarding)

### **Проблема, которую решает perfect forwarding**

```cpp
// ❌ НЕПРАВИЛЬНО: теряется информация о lvalue/rvalue
template<typename T>
void wrong_forward(T arg) {
    target(arg);  // Всегда передаём как lvalue!
}

// ✅ Правильно с универсальными ссылками и std::forward
template<typename T>
void perfect_forward(T&& arg) {
    target(std::forward<T>(arg));  // Сохраняем категорию значения
}

void target(int&);   // Перегрузка для lvalue
void target(int&&);  // Перегрузка для rvalue

int x = 5;
wrong_forward(x);        // Вызывает target(int&) - OK
wrong_forward(10);       // Тоже вызывает target(int&) - ПРОБЛЕМА!
wrong_forward(std::move(x)); // Тоже target(int&) - ПРОБЛЕМА!

perfect_forward(x);        // target(int&) - OK
perfect_forward(10);       // target(int&&) - OK!
perfect_forward(std::move(x)); // target(int&&) - OK!
```

### **Как работает std::forward**

```cpp
// Упрощённая реализация std::forward
template<typename T>
T&& forward(typename std::remove_reference<T>::type& arg) noexcept {
    return static_cast<T&&>(arg);  // Здесь применяются правила свёртывания!
}

template<typename T>
T&& forward(typename std::remove_reference<T>::type&& arg) noexcept {
    return static_cast<T&&>(arg);
}
```

## Сравнение std::move и std::forward

| Аспект | `std::move` | `std::forward` |
|--------|-------------|----------------|
| **Назначение** | Безусловный каст к rvalue | Условный каст, сохраняет категорию значения |
| **Возвращаемый тип** | Всегда `T&&` | `T&&` (но T может быть lvalue-ссылкой) |
| **Когда использовать** | Когда хотим переместить ресурсы | В шаблонах для perfect forwarding |
| **Зависимость от контекста** | Нет | Да (зависит от выведенного типа T) |
| **Эквивалент** | `static_cast<T&&>` | `static_cast<T&&>` с учётом свёртывания |

### **Правила использования**:

```cpp
// Правило 1: Используйте std::move только с rvalue-ссылками
class Widget {
    std::string data;
public:
    Widget(Widget&& other) 
        : data(std::move(other.data)) {}  // OK: other - rvalue-ссылка
    
    Widget& operator=(Widget&& other) {
        data = std::move(other.data);      // OK
        return *this;
    }
    
    void setData(const std::string& newData) {
        data = newData;                    // Копирование
    }
    
    void setData(std::string&& newData) {
        data = std::move(newData);         // Перемещение - OK
    }
};

// Правило 2: Используйте std::forward только с универсальными ссылками
template<typename T>
void factory(T&& arg) {
    // Создаём объект, сохраняя категорию значения аргумента
    Product p(std::forward<T>(arg));
}

// Правило 3: Не используйте std::move с универсальными ссылками
template<typename T>
void bad_idea(T&& arg) {
    // ❌ ПЛОХО: аргумент мог быть lvalue, но мы его перемещаем
    store(std::move(arg));
}

template<typename T>
void careful(T&& arg) {
    // ✅ ХОРОШО: только если мы точно знаем, что arg больше не нужен
    if (/* условие, что можно перемещать */) {
        store(std::move(arg));
    } else {
        store(arg);  // Копирование
    }
}
```

## Практические примеры

### 1. **Реализация make_unique/make_shared**

```cpp
template<typename T, typename... Args>
std::unique_ptr<T> make_unique(Args&&... args) {
    // Perfect forwarding всех аргументов в конструктор T
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

class MyClass {
public:
    MyClass(int a, const std::string& b, std::vector<int>&& c) {}
};

// Все аргументы передаются с сохранением их категорий
auto obj = make_unique<MyClass>(
    42,                    // int (передаётся по значению)
    "hello",               // const char* → const std::string&
    std::vector<int>{1,2,3} // rvalue → std::vector<int>&&
);
```

### 2. **Wrapper-классы с perfect forwarding**

```cpp
template<typename T>
class Wrapper {
    T value;
public:
    // Конструктор с perfect forwarding
    template<typename U>
    explicit Wrapper(U&& val) 
        : value(std::forward<U>(val)) {}
    
    // Метод с perfect forwarding
    template<typename U>
    void setValue(U&& newVal) {
        value = std::forward<U>(newVal);
    }
};

Wrapper<std::string> w1("test");  // Конструктор перемещения
std::string s = "hello";
Wrapper<std::string> w2(s);       // Конструктор копирования

w1.setValue(std::move(s));        // Оператор перемещения
w2.setValue("world");             // Конструктор перемещения из временного
```

### 3. **Variadic templates + perfect forwarding**

```cpp
// Вариативный шаблон с perfect forwarding
template<typename... Args>
void log_and_call(const std::string& func_name, Args&&... args) {
    std::cout << "Calling " << func_name << "\n";
    
    // Передаём все аргументы с сохранением категорий
    some_function(std::forward<Args>(args)...);
}
```

### 4. **Проблема с перегрузкой универсальных ссылок**

```cpp
// ❌ ПРОБЛЕМА: универсальная ссылка слишком "жадная"
template<typename T>
void process(T&& value) {
    // ...
}

// Перегрузка для int
void process(int value) {
    // ...
}

process(42);  // Неоднозначность! Обе функции подходят

// ✅ РЕШЕНИЕ: Использовать SFINAE или концепты
template<typename T>
auto process(T&& value)
    -> std::enable_if_t<!std::is_same_v<std::decay_t<T>, int>>
{
    // ...
}
```

## Оптимизации компилятора

```cpp
// RVO (Return Value Optimization) и NRVO
std::vector<int> create() {
    std::vector<int> result{1, 2, 3};
    return result;  // Компилятор может убрать копирование
}

auto v = create();  // Создаётся напрямую в v

// Copy elision (удаление копий) - даже до C++17
std::string make_string() {
    return std::string("hello");  // Конструктор может быть пропущен
}

// Move семантика VS RVO
std::vector<int> with_move() {
    std::vector<int> v = {1, 2, 3};
    return std::move(v);  // ❌ ПЛОХО: мешает RVO!
    // Лучше просто: return v;
}
```

## Идиомы и паттерны

### 1. **Copy-and-swap**

```cpp
class Resource {
    int* data;
public:
    // Конструктор перемещения через swap
    Resource(Resource&& other) noexcept 
        : data(nullptr) {
        swap(*this, other);
    }
    
    // Оператор присваивания перемещением через swap
    Resource& operator=(Resource&& other) noexcept {
        swap(*this, other);
        return *this;
    }
    
    // Универсальный оператор присваивания
    Resource& operator=(Resource other) noexcept {
        swap(*this, other);
        return *this;
    }
    
    friend void swap(Resource& a, Resource& b) noexcept {
        using std::swap;
        swap(a.data, b.data);
    }
};
```

### 2. **Emplace-методы в контейнерах**

```cpp
std::vector<std::pair<int, std::string>> vec;

// Старый способ: создание временного объекта + перемещение
vec.push_back(std::make_pair(42, "hello"));

// Новый способ: perfect forwarding прямо в конструктор
vec.emplace_back(42, "hello");  // Нет временных объектов!
```

### 3. **Политика передачи по значению для sink-параметров**

```cpp
// Для sink-параметров (которые сохраняются в классе)
class Widget {
    std::string name;
public:
    // Принимаем по значению, затем перемещаем
    void setName(std::string newName) {
        name = std::move(newName);
    }
};

Widget w;
std::string s = "test";
w.setName(s);            // Копирование в параметр, затем перемещение
w.setName("hello");      // Конструктор из временного, затем перемещение
w.setName(std::move(s)); // Перемещение в параметр, затем перемещение
```

## Итог

**Свёртывание ссылок** - это механизм, который делает возможными:
- Универсальные ссылки (`T&&` с выводом типа)
- Perfect forwarding через `std::forward`
- Корректную работу шаблонов с ссылочными типами

**Move-Forward семантика** решает ключевые проблемы:
- **Move семантика**: эффективный перенос ресурсов из временных объектов
- **Perfect forwarding**: сохранение категории значения (lvalue/rvalue) при передаче через шаблонные функции

**Золотые правила**:
1. Используйте `std::move` только с rvalue-ссылками
2. Используйте `std::forward` только с универсальными ссылками
3. Не мешайте компилятору делать RVO
4. Пишите конструкторы и операторы перемещения как `noexcept`
5. Используйте perfect forwarding в фабриках и wrapper-ах