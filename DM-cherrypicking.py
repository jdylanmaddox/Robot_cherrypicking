from opentrons import protocol_api
import pandas as pd
from io import StringIO

# metadata
metadata = {
    'protocolName': 'Cherrypicking from .csv',
    'author': 'Dylan Maddox',
    'source': 'Opentrons',
    'apiLevel': '2.13'
}

def run(ctx):
    # turn on lights
    ctx.set_rail_lights(True)

    # select labware
    plate_type = 'plate_type_variable'
    tip_type = 'tip_type_variable'

    # load labware
    source_plate1 = ctx.load_labware(plate_type, 1, 'Source Plate 1')
    source_plate2 = ctx.load_labware(plate_type, 2, 'Source Plate 2')
    source_plate3 = ctx.load_labware(plate_type, 3, 'Source Plate 3')
    source_plate4 = ctx.load_labware(plate_type, 4, 'Source Plate 4')
    source_plate5 = ctx.load_labware(plate_type, 5, 'Source Plate 5')
    source_plate6 = ctx.load_labware(plate_type, 6, 'Source Plate 6')
    source_plate7 = ctx.load_labware(plate_type, 7, 'Source Plate 7')
    source_plates = [source_plate1, source_plate2, source_plate3, source_plate4,
                     source_plate5, source_plate6, source_plate7]

    destination_plate1 = ctx.load_labware(plate_type, 8, 'Destination Plate 1')
    destination_plate2 = ctx.load_labware(plate_type, 9, 'Destination Plate 2')
    destination_plates = [destination_plate1, destination_plate2]

    sample_vol = float('sample_vol_variable')

    # load tipracks
    if (sample_vol <= 20) and (tip_type == 'not_filtered'):
        tiprack20 = [ctx.load_labware('opentrons_96_tiprack_20ul', slot, '20ul tiprack')
                     for slot in ['10', '11']]
        p20 = ctx.load_instrument('p20_single_gen2', 'right', tip_racks=tiprack20)
    elif (sample_vol > 20) and (tip_type == 'not_filtered'):
        tiprack300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot, '300ul tiprack')
                      for slot in ['10', '11']]
        p300 = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=tiprack300)
    elif (sample_vol <= 20) and (tip_type == 'filtered'):
        tiprack20 = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot, '20ul filtered tiprack')
                     for slot in ['10', '11']]
        p20 = ctx.load_instrument('p20_single_gen2', 'right', tip_racks=tiprack20)
    elif (sample_vol > 20) and (tip_type == 'filtered'):
        tiprack300 = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot, '200ul filtered tiprack')
                      for slot in ['10', '11']]
        p300 = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=tiprack300)

    # load data
    data = '''
    CHERRY_DATA
    '''
    cherrypicked = pd.read_csv(StringIO(data), sep='\s+')

    # import csv
    # cherrypicked = pd.read_csv('./output_files/test_cherrypicked.csv')

    # Iterate over rows using DataFrame.itertuples()
    for row in cherrypicked.itertuples(index=True):
        plate_num = (getattr(row, "plate_num")) - 1  # must subtract 1 for 0-based indexing
        cherry_plate_num = (getattr(row, "cherry_plate_num")) - 1  # must subtract 1 for 0-based indexing
        source_well = (getattr(row, "plate_well"))
        cherry_well = (getattr(row, "cherry_well"))
        liquid = (getattr(row, "sample_vol"))
        source = source_plates[plate_num].wells_by_name()[source_well]  # shortcut for pipetting
        destination = destination_plates[cherry_plate_num].wells_by_name()[cherry_well]    # shortcut for pipetting
        pip = p300 if liquid > 20 else p20
        pip.pick_up_tip()
        pip.aspirate(liquid, source)
        pip.dispense(liquid, destination)
        pip.blow_out(destination.bottom(2))
        pip.drop_tip()
