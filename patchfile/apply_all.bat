@echo off
setlocal
set "ROOT=%~dp0.."
set "PYTHONPATH=%ROOT%;%ROOT%\src;%ROOT%\.pylibs;%ROOT%\tests\figground"
cd /d "%ROOT%"

echo [1/3] Building overlay...
python "%~dp0apply_fixes.py" || goto :fail

echo [2/3] Mechanism checks...
set "PYTHONPATH=%ROOT%\phase2\build\src;%ROOT%;%ROOT%\.pylibs;%ROOT%\tests\figground"
python "%~dp0verify_overlay.py" || goto :fail

echo [3/3] Re-baselined pins...
set "PYTHONPATH=%ROOT%\phase2\build\tests\figground;%ROOT%\phase2\build\src;%ROOT%;%ROOT%\.pylibs;%ROOT%\phase2;%ROOT%\phase2\build\tests\matcher"
python -m pytest -p phase2_harness --import-mode=importlib -q ^
  "%~dp0build\tests\matcher\test_p4b_count_apart.py" ^
  "%~dp0build\tests\matcher\test_phase2_flagged_mechanisms.py" ^
  "%~dp0build\tests\matcher\test_relation_frame_emitted.py" ^
  "%~dp0build\tests\matcher\test_declared_defaults.py" ^
  "%~dp0build\tests\matcher\test_relation_frame_partition.py" ^
  "%~dp0build\tests\matcher\test_relational_agreement_symmetry.py" ^
  "%~dp0build\tests\matcher\test_bridge_and_contour_contracts.py" ^
  "%~dp0build\tests\matcher\test_materialize_template_exact.py"
if errorlevel 1 goto :fail

echo.
echo PHASE 2 OVERLAY: GREEN
echo Patched tree: %~dp0build\src
echo Originals:    %ROOT%\src  (unchanged)
exit /b 0

:fail
echo.
echo PHASE 2 OVERLAY: RED
exit /b 1
