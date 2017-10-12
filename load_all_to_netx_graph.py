import csv
import networkx as nx

Gph = nx.Graph()
DBS_PATH = '/Users/ramintakin/Parkway_Drive/Trade_finance/Technology/SIC_HS_tool/'

for action in ['Ex', 'Im']:
    sourcedata = DBS_PATH+action+'port_combined_summary_test.csv'
    with open(sourcedata, 'r') as tsvfile:
        tsvin = csv.reader(tsvfile, delimiter='\t')
        # Adjust row[] indices depending on if sourcedata has
        # EITHER 5, 3, 5, 3, 7
        # [' CompanyNumber', 'RegAddress.PostCode', 'Postcode', 'HScode',
        # 'co_name', 'Name', 'SICCode.SicText_1', 'MonthCount']
        # OR 2, 1, 2, 1, 3 for
        # ['Postcode', 'HScode', 'Name', 'MonthCount']
        for i, row in enumerate(tsvin):
            # if i < 100000:
            if (row[1][-6:]!='000000'):
                Gph.add_node(row[2], type='Name', postcode=row[0])
                Gph.add_node(row[1], type='Commodity')
                Gph.add_edge(row[2], row[1], 
                    direction=action+'ported', monthcount=row[3])

nx.write_gml(Gph,DBS_PATH+'impex_full.graphml')

