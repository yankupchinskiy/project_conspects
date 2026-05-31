# lvalue и rvalue ссылки в C++

## Основные понятия

### **lvalue-ссылки** (обычные ссылки)
Ссылки на объекты, которые имеют адрес в памяти и существуют продолжительное время.

```cpp
int x = 10;
int& ref = x;  // lvalue-ссылка
ref = 20;      // изменяет x
```

### **rvalue-ссылки** (C++11 и новее)
Ссылки на временные объекты, которые можно "опустошить" (переместить ресурсы).

```cpp
int&& rref = 10;          // rvalue-ссылка на временный объект
std::string&& sref = std::string("hello");  // rvalue-ссылка
```

## Сравнительная таблица

| Характеристика | lvalue-ссылка | rvalue-ссылка |
|----------------|---------------|---------------|
| **Синтаксис** | `T&` | `T&&` |
| **Может связываться с** | lvalue (и const rvalue) | rvalue (xvalue, prvalue) |
| **Продлевает жизнь временного** | Только const lvalue-ссылка | Да |
| **Основное назначение** | Псевдоним, избегание копирования | Семантика перемещения, perfect forwarding |
| **Модификация объекта** | Разрешает (если не const) | Разрешает (часто "опустошает") |
| **Время жизни объекта** | Должно превышать время жизни ссылки | Может быть временным |

## Особенности lvalue-ссылок

### 1. **Связывание только с lvalue**
```cpp
int x = 5;
int& ref1 = x;     // OK
int& ref2 = 10;    // ОШИБКА: не может связываться с rvalue
int& ref3 = x + 1; // ОШИБКА: результат выражения - rvalue
```

### 2. **Const lvalue-ссылки могут связываться с rvalue**
```cpp
const int& cref1 = 10;    // OK
const int& cref2 = x + 1; // OK

std::string func();
const std::string& sref = func(); // OK, продлевает жизнь временного
```

### 3. **Не могут быть неинициализированными**
```cpp
int& ref; // ОШИБКА: должна быть инициализирована
```

### 4. **Не могут менять привязку**
```cpp
int x = 5, y = 10;
int& ref = x;
ref = y;  // Не перенаправляет ссылку, а КОПИРУЕТ значение y в x
// ref по-прежнему ссылается на x
```

### 5. **Использование в функциях**
```cpp
// Передача по ссылке (без копирования)
void process(std::vector<int>& vec) {
    vec.push_back(42);
}

// Возврат по ссылке
int& getElement(std::vector<int>& vec, size_t idx) {
    return vec[idx];
}

std::vector<int> v = {1, 2, 3};
getElement(v, 1) = 99;  // Изменяет второй элемент
```

## Особенности rvalue-ссылок

### 1. **Связываются только с rvalue**
```cpp
int x = 5;
int&& rref1 = 10;            // OK: prvalue
int&& rref2 = x + 1;         // OK: результат выражения
int&& rref3 = std::move(x);  // OK: xvalue (после std::move)
int&& rref4 = x;             // ОШИБКА: не может связываться с lvalue
```

### 2. **Продлевают жизнь временного объекта**
```cpp
std::string&& sref = std::string("Hello");  
// Временный объект живет, пока живет sref
sref += " World";  // Можно модифицировать
```

### 3. **Ключевая роль в семантике перемещения**
```cpp
class Buffer {
    int* data;
    size_t size;
public:
    // Конструктор перемещения
    Buffer(Buffer&& other) noexcept 
        : data(other.data), size(other.size) {
        other.data = nullptr;  // "Опустошаем" исходный объект
        other.size = 0;
    }
    
    // Оператор присваивания с перемещением
    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data;
            data = other.data;
            size = other.size;
            other.data = nullptr;
            other.size = 0;
        }
        return *this;
    }
};
```

### 4. **Использование с std::move**
```cpp
std::string createString() {
    return "Hello";
}

std::string s1 = "Hello";
std::string s2 = std::move(s1);  
// s1 становится "опустошенным" (valid but unspecified state)
// s2 получает ресурсы s1

// После std::move(s1):
// - s1 всё еще существует
// - Нельзя полагаться на его значение
// - Можно переназначить: s1 = "New value"
```

## Универсальные ссылки (Universal References)

**Важное исключение:** `T&&` в шаблонах может быть как rvalue, так и lvalue-ссылкой.

```cpp
template<typename T>
void func(T&& param) {  // УНИВЕРСАЛЬНАЯ ссылка
    // param может быть lvalue или rvalue ссылкой
}

int x = 10;
func(x);   // T = int&,  param = int&  (lvalue ссылка)
func(10);  // T = int,   param = int&& (rvalue ссылка)
```

### Perfect Forwarding
```cpp
template<typename T>
void wrapper(T&& arg) {
    // Передаем arg дальше с сохранением категории значения
    process(std::forward<T>(arg));
}

wrapper(x);              // lvalue передается как lvalue
wrapper(10);             // rvalue передается как rvalue
wrapper(std::move(x));   // xvalue передается как rvalue
```

## Правила разрешения перегрузок

### Пример с перегрузкой по категории значения:
```cpp
void process(int& x) {
    std::cout << "lvalue: " << x << std::endl;
}

void process(const int& x) {
    std::cout << "const lvalue: " << x << std::endl;
}

void process(int&& x) {
    std::cout << "rvalue: " << x << std::endl;
}

int main() {
    int a = 5;
    const int b = 10;
    
    process(a);           // lvalue
    process(b);           // const lvalue  
    process(20);          // rvalue
    process(a + b);       // rvalue
    process(std::move(a)); // rvalue
}
```

## Ссылочные квалификаторы для методов

Можно перегружать методы в зависимости от категории объекта:

```cpp
class Widget {
    std::string data;
public:
    // Вызывается только для lvalue-объектов
    std::string& get() & {
        return data;
    }
    
    // Вызывается только для rvalue-объектов
    std::string&& get() && {
        return std::move(data);
    }
    
    // Вызывается для const lvalue-объектов
    const std::string& get() const & {
        return data;
    }
};

Widget w;
auto s1 = w.get();      // копирование (вызывается & версия)

auto s2 = Widget().get(); // перемещение (вызывается && версия)
```

## Временные материализации

```cpp
int&& r = 10 + 20;  // 1. prvalue (10+20)
                    // 2. Временная материализация в xvalue
                    // 3. Связывание с rvalue-ссылкой
                    // 4. Продление жизни до конца scope
```

## Опасности и подводные камни

### 1. **Возврат ссылки на локальный объект**
```cpp
int& badFunction() {
    int x = 10;
    return x;  // КАТАСТРОФА: висячая ссылка
}

std::string&& alsoBad() {
    return "hello";  // ОШИБКА: возвращает ссылку на временный
}
```

### 2. **Неоправданное использование std::move**
```cpp
std::string createString() {
    std::string s = "Hello";
    return std::move(s);  // ПЛОХО: мешает RVO (Return Value Optimization)
    // Лучше: return s;
}
```

### 3. **Перемещение из const объектов**
```cpp
const std::string cs = "Hello";
std::string s = std::move(cs);  // Не перемещение, а КОПИРОВАНИЕ!
// std::move(const T&) возвращает const T&&, что не позволяет перемещать
```

## Практические примеры

### 1. **Эффективная вставка в контейнер**
```cpp
std::vector<std::string> vec;
std::string largeString = "очень длинная строка...";

// Вставка копированием (дорого)
vec.push_back(largeString);

// Вставка перемещением (дешево)
vec.push_back(std::move(largeString));

// Прямая вставка временного объекта (оптимально)
vec.push_back("новая строка");
vec.emplace_back("еще строка");  // создание на месте
```

### 2. **Фабричные функции с перемещением**
```cpp
class Factory {
    std::vector<int> cache;
public:
    std::vector<int> getData() {
        // Возвращаем перемещением, если можно
        if (cache.empty()) {
            return generateData();
        } else {
            return std::move(cache);  // Перемещаем кэш
        }
    }
};
```

### 3. **Обмен ресурсов без копирования**
```cpp
void swap(Buffer& a, Buffer& b) noexcept {
    Buffer temp = std::move(a);  // перемещение из a
    a = std::move(b);            // перемещение из b в a
    b = std::move(temp);         // перемещение из temp в b
    // Ни одного копирования!
}
```

## Правила хорошего тона

1. **Используйте const lvalue-ссылки** для параметров, которые только читаются
2. **Используйте rvalue-ссылки** для реализации семантики перемещения
3. **Возвращайте по значению** из функций (компилятор оптимизирует)
4. **Избегайте возврата ссылок**, если нет уверенности в времени жизни объекта
5. **Применяйте std::move** только когда нужно явно передать владение ресурсами
6. **Не используйте std::move** с локальными переменными при возврате из функции

## Заключение

Понимание различий между lvalue и rvalue ссылками критически важно для:
- **Эффективности**: избегание лишних копирований
- **Безопасности**: правильное управление временем жизни
- **Оптимизации**: использование семантики перемещения
- **Универсальности**: perfect forwarding в шаблонах

**Простые правила:**
- `T&` — для именованных объектов, которые должны жить дольше
- `T&&` — для временных объектов или явного перемещения
- `const T&` — для чтения без копирования, работает с любыми значениями