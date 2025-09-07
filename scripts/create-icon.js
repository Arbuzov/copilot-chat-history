const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

// Конвертируем SVG в PNG правильного размера для маркетплейсов
const createIconPng = async () => {
  try {
    const svgPath = path.join(__dirname, '..', 'resources', 'icon.svg');
    const pngPath = path.join(__dirname, '..', 'resources', 'icon.png');
    
    console.log('📐 Converting SVG to PNG (128x128)...');
    
    await sharp(svgPath)
      .resize(128, 128)
      .png({
        compressionLevel: 0, // No compression for maximum file size
        quality: 100,        // Maximum quality
        palette: false,      // Full color, not indexed
        progressive: false,  // Standard PNG
        force: true         // Force PNG output
      })
      .toFile(pngPath);
    
    // Проверяем размер файла
    const stats = fs.statSync(pngPath);
    console.log(`✅ Icon created: ${pngPath}`);
    console.log(`📊 File size: ${(stats.size / 1024).toFixed(2)} KB`);
    console.log(`📐 Dimensions: 128x128 pixels`);
    
    // VS Code требует минимум 1KB для иконки
    if (stats.size < 1024) {
      console.warn('⚠️  Warning: Icon file size is less than 1KB, marketplace might not display it properly');
    } else {
      console.log('✅ Icon size is suitable for VS Code Marketplace');
    }
    
  } catch (error) {
    console.error('❌ Error creating icon:', error.message);
    process.exit(1);
  }
};

if (require.main === module) {
  createIconPng();
}

module.exports = { createIconPng };
