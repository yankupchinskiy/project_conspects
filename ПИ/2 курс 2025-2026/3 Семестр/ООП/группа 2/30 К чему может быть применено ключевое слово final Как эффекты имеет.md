### 30. Ключевое слово `final`

Применяется к:

1. **Классам**: запрещает наследование
``` C++
    class Base final { };
    class Derived : public Base { }; // Ошибка
```
2. **Методам**: запрещает переопределение
```C++
    virtual void method() final;
```