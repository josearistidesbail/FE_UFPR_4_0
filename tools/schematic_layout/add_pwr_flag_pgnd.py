#!/usr/bin/env python3
"""S11 (2026-09-23), run once: add a PWR_FLAG on PGND_MOD at the NT2 star (power sheet)
so ERC stops reporting power_pin_not_driven on U4 pin 1 (-Vin).
  python3 add_pwr_flag_pgnd.py SRC power.kicad_sch DST power.kicad_sch
Flag pin at (26.67, 110.49) = the PGND_MOD global label + wire end at NT2 pin 1, rotated 180
(points down, away from the NT2 reference text)."""
import sys, uuid
t = open(sys.argv[1]).read()
assert '"#FLG07"' not in t and t.count('(sheet_instances') == 1
assert '(global_label "PGND_MOD"\n\t\t(shape bidirectional)\n\t\t(at 26.67 110.49 180)' in t
X, Y = '26.67', '110.49'
blk = f'''	(symbol
		(lib_id "FE_UFPR_4_0:PWR_FLAG")
		(at {X} {Y} 180)
		(unit 1)
		(body_style 1)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(in_pos_files yes)
		(dnp no)
		(uuid "{uuid.uuid4()}")
		(property "Reference" "#FLG07"
			(at {X} 116.84 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Value" "PWR_FLAG"
			(at {X} 114.3 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Footprint" ""
			(at {X} {Y} 0)
			(hide yes)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Datasheet" ""
			(at {X} {Y} 0)
			(hide yes)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(property "Description" "Special symbol for telling ERC where power comes from"
			(at {X} {Y} 0)
			(hide yes)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
			)
		)
		(pin "1"
			(uuid "{uuid.uuid4()}")
		)
		(instances
			(project "FE_UFPR_4_0"
				(path "/0cde0ae3-e31e-4592-8212-8a072a248a80/6442f421-491d-4bfb-bee7-d0b4e843a827"
					(reference "#FLG07")
					(unit 1)
				)
			)
		)
	)
'''
i = t.index('\t(sheet_instances')
open(sys.argv[2], 'w').write(t[:i] + blk + t[i:])
print('PWR_FLAG #FLG07 inserted at', X, Y)
