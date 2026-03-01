@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   VoluStack Release Creator
echo ========================================
echo.

REM Show existing tags
echo Existing tags:
git tag -l "v*"
echo.

REM Prompt for version
set /p NEW_VERSION="Enter new version (e.g., 1.0.0): "
if "%NEW_VERSION%"=="" (
    echo ERROR: Version cannot be empty!
    pause
    exit /b 1
)

echo.
echo Creating release v%NEW_VERSION%...
echo.

REM [1/5] Update version.py
echo [1/5] Updating version.py...
echo __version__ = "%NEW_VERSION%"> volustack\version.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to update version.py
    pause
    exit /b 1
)

REM [2/5] Update Inno Setup script
echo [2/5] Updating VoluStack.iss version...
powershell -Command "(Get-Content installer\VoluStack.iss) -replace '#define MyAppVersion \".*\"', '#define MyAppVersion \"%NEW_VERSION%\"' | Set-Content installer\VoluStack.iss"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to update VoluStack.iss
    pause
    exit /b 1
)

REM [3/5] Commit changes
echo [3/5] Committing version bump...
git add volustack\version.py installer\VoluStack.iss
git commit -m "Bump version to %NEW_VERSION%"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to commit changes
    pause
    exit /b 1
)

REM [4/5] Create tag
echo [4/5] Creating tag v%NEW_VERSION%...
git tag -a v%NEW_VERSION% -m "Release version %NEW_VERSION%"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create tag
    pause
    exit /b 1
)

REM [5/5] Push
echo [5/5] Pushing to origin...
git push origin main
git push origin v%NEW_VERSION%
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to push to origin
    pause
    exit /b 1
)

echo.
echo ========================================
echo   RELEASE v%NEW_VERSION% CREATED!
echo ========================================
echo.
echo GitHub Actions will now build and release.
echo Check: https://github.com/OOMrConrado/VoluStack/actions
echo.
pause
