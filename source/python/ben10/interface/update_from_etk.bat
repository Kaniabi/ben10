:: This script does not fully updates ben10's code, but it gives a hint if
:: we have any new changes in the original code.
copy /qes x:\etk\coilib50\source\python\coilib50\basic\interface\_adaptable_interface.py
::_interface: Removed ScalarAttribute on ben10.
call aa.bat .fix_format . --refactor=update_from_etk.ini
call aa.bat .fix_format . --refactor=x:\ben10\terraforming.ini


