const fs = require('fs');
const path = require('path');

// Создаем простую PNG иконку программно
const createIconPng = () => {
  // Для простоты используем placeholder файл
  // В реальном проекте лучше использовать инструмент конвертации SVG в PNG
  console.log('Icon placeholder created. Please replace resources/icon.png with actual 128x128 PNG icon.');
};

if (require.main === module) {
  createIconPng();
}
