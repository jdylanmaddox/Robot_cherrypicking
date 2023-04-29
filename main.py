from create_cherrypicking_protocol import cherrypick

cherrypick(base_name='test_02',  # basename of output files
           sample_vol=10.0,  # in uL
           plate_type='nest_96_wellplate_100ul_pcr_full_skirt',
           tip_type='filtered',  # 'filtered' or 'not_filtered'
           excel_file='yes',  # 'yes' or 'no'
           simulate_run='yes'  # 'yes' or 'no'
           )


