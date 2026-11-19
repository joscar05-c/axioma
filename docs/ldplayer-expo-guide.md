# Guía para probar Axioma Mobile en LDPlayer (Windows)

Esta guía permite levantar la app móvil de **Axioma** (**Expo SDK 52**) dentro de **LDPlayer** en cualquier PC con Windows sin depender de `npm run android`.

> **¿Por qué no usar `npm run android` (`expo start --android`) con LDPlayer?**
> LDPlayer aparece en `adb devices` como `emulator-5554` y `127.0.0.1:5555`. Expo CLI intenta ejecutar `adb -s emulator-5554 emu avd name` sobre el puerto `5554` esperando un emulador de Android Studio, pero LDPlayer no expone esa consola y rechaza la conexión (error `10061`). Conectando directamente a `127.0.0.1:5555` funciona sin problemas.

---

## 1. Requisitos previos en la PC (ej. PC de casa)

1. Tener **Node.js** instalado y **LDPlayer 9 (64 bits)**.
2. Instalar dependencias y preparar el `.env` móvil (ya apunta al backend desplegado en Vercel):
   ```powershell
   cd mobile
   npm install
   copy .env.example .env
   ```
3. Activar depuración ADB en LDPlayer:
   - Abre **Ajustes** (ícono de engranaje en LDPlayer) → **Otros ajustes** → **Depuración ADB** → selecciona **Abrir conexión local** y reinicia LDPlayer.

---

## 2. Elegir el ejecutable `adb.exe`

- **Si tienes Android Studio instalado:**
  ```powershell
  $adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
  ```
- **Si NO tienes Android Studio instalado en esa PC**, puedes usar el `adb.exe` que ya incluye LDPlayer (ajusta la ruta si lo instalaste en otro disco):
  ```powershell
  $adb = "C:\LDPlayer\LDPlayer9\adb.exe"
  ```

Verifica la conexión con LDPlayer abierto:
```powershell
& $adb connect 127.0.0.1:5555
& $adb devices
```
Debes ver `127.0.0.1:5555   device`.

---

## 3. Instalación única de Expo Go (SDK 52) en LDPlayer

Este paso solo se hace **una vez** en cada emulador nuevo:

```powershell
$apk = "$env:TEMP\Expo-Go-2.32.20.apk"
Invoke-WebRequest -Uri "https://github.com/expo/expo-go-releases/releases/download/Expo-Go-2.32.20/Expo-Go-2.32.20.apk" -OutFile $apk
& $adb -s 127.0.0.1:5555 install -r $apk
& $adb -s 127.0.0.1:5555 shell pm list packages host.exp.exponent
```

Debe imprimir `package:host.exp.exponent`.

---

## 4. Arranque diario para probar cambios

1. **Terminal 1** — En `mobile/`, inicia solo Metro Bundler:
   ```powershell
   cd mobile
   npm start
   ```
2. **Terminal 2** — Abre el túnel del puerto `8081` y lanza Axioma en Expo Go dentro de LDPlayer:
   ```powershell
   $adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" # o C:\LDPlayer\LDPlayer9\adb.exe
   & $adb -s 127.0.0.1:5555 connect 127.0.0.1:5555
   & $adb -s 127.0.0.1:5555 reverse tcp:8081 tcp:8081
   & $adb -s 127.0.0.1:5555 shell am start -a android.intent.action.VIEW -d "exp://127.0.0.1:8081" host.exp.exponent
   ```

---

## Solución rápida de problemas
- **No aparece `127.0.0.1:5555` en `adb devices`:** asegúrate de tener abierta la instancia de LDPlayer y ejecuta `& $adb connect 127.0.0.1:5555`.
- **Conflicto entre `adb` de Android Studio y el de LDPlayer:** usa siempre el mismo `adb.exe` en toda la sesión (si cambiaste entre uno y otro, ejecuta `& $adb kill-server` y vuelve a conectar).
- **La app dice no poder conectarse a `127.0.0.1:8081`:** vuelve a ejecutar `& $adb -s 127.0.0.1:5555 reverse tcp:8081 tcp:8081` y recarga dentro de Expo Go (`r` en la terminal de Metro).
