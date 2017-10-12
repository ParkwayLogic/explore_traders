#!/usr/bin/env python
from json import dumps
from flask import Flask, Response, request
import networkx as nx
import utils
import pandas

app = Flask(__name__, static_url_path='/static/')
print("Loading app", app.name)

# @app.teardown_appcontext
# def close_db(error):
#     global NETX_DB
#     del NETX_DB
#     print('App teardown', app.name)

@app.route("/")
def get_index():
    return app.send_static_file('index.html')

@app.route("/companies")
def get_companies():
    max_entries = 50
    query = request.args['q'].upper()
    entry = []
    OUTPUT = {}
    global NETX_DB
    for x in nx.get_node_attributes(NETX_DB, 'type'):
        if query in x:
            entry.append({'name': x})
    if len(entry) > max_entries:
        entry.insert(0, {'name': 'More available. Keep typing to narrow down...'})
        OUTPUT['names'] = entry[:max_entries]
    else:
        OUTPUT['names'] = entry
    return Response(dumps(OUTPUT), mimetype="application/json")

@app.route("/HS_tool")
def get_product_friendly():
    code = request.args['cn1']
    # global DBS_PATH
    # lookup_table = pandas.read_csv(DBS_PATH+'HS2_names_ref.txt', sep='\t', 
    #     dtype={'HS2': str, 'HS2Desc': str}, warn_bad_lines=True)
    # chap = utils._make_8char_CN(code)   #[:2]
    desc = code+'0'   # only this needed if checking against the full-detail DB
    # rows_bool = (lookup_table['HS2']==chap)
    # desc = lookup_table.loc[rows_bool,'HS2Desc'].values[0]
    return Response(get_product_totals_from_file(desc), 
        mimetype="application/json")

def get_product_totals_from_file(desc):
    """
    Returns in json format, totals for variables displayed by HS Country tool
    argument desc is the friendly name for the tariff Section
    """
    colnames = [
        'ProdName', 'Destination', 'DESTA',
        'CSub320k', 'VSub320k', 'C320k1m', 'V320k1m', 'C1m16m', 'V1m16m',
        'CLarger', 'VLarger', 'CSmalls', 'VSmalls', 'CLarges', 'VLarges',
        'CIPROPRsub1m', 'CIPROPRLarger', 'Reexsub1m', 'ReexLarger', 'AirLHR',
        'OtherAir', 'Sea'
    ] 
    #  'Region', 'RegionCount', 'RegionValue',
    # 'Status', 'Treaty', 'TreatyCountries', 'TreatyDate', 'TreatyLink',
    coltypes = [
        'str', 'str', 'str', 
        'float', 'float', 'float', 'float', 'float', 'float', 
        'float', 'float', 'float', 'float', 'float', 'float', 
        'float', 'float', 'float', 'float', 'float', 
        'float', 'float'
    ]
    # 'str', 'int', 'int',
    # 'str', 'str', 'str', 'str', 'str',
    colnas = [
        '-', '-', '-',
        0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0
    ]
    # '-', 0, 0,
    # '-', '-', '-', '-', '-', 
    assert len(colnames)==len(coltypes)==len(colnas)
    # coltypesdict = dict(zip(colnames, coltypes))
    coltypesdict = {}
    fields_list = ['CSub320k', 'VSub320k', 'C320k1m',
       'V320k1m', 'C1m16m', 'V1m16m', 'CLarger', 'VLarger', 'CSmalls',
       'VSmalls', 'CLarges', 'VLarges', 'CIPROPRsub1m', 'CIPROPRLarger',
       'Reexsub1m', 'ReexLarger', 'AirLHR', 'OtherAir', 'Sea']
    for field in fields_list:
        coltypesdict[field] = lambda x: utils.conv_to_int(x)
    global DBS_PATH
    hs_lookup_table = pandas.read_csv(
        DBS_PATH+'HS-country-tool-updated-201710.csv', sep=',', 
        warn_bad_lines=True, index_col=0, converters=coltypesdict)
    # keep_default_na=False, na_values=["NA"], na_filter=False, dtype=coltypesdict,
    hs_lookup_table.fillna(value=dict(zip(colnames, colnas)), inplace=True)
    rows_bool = hs_lookup_table['ProdName'].map(
        lambda x: True if (int(x)==int(desc)) else False)
    relevant_rows = hs_lookup_table[rows_bool]
    columns_list = [
        'VSmalls', 'VLarges', 'CSmalls', 'CLarges',
        'AirLHR', 'OtherAir', 'Sea', 
        'CIPROPRsub1m', 'CIPROPRLarger', 'Reexsub1m', 'ReexLarger'
    ]  # 'ContCAll',
    out_col_headings = [
        'SumVSmalls', 'SumVLarges', 'SumCSmalls', 'SumCLarges',
        'SumAirLHR', 'SumOtherAir', 'SumSea', 
        'SumCIPROPRsub1m', 'SumCIPROPRLarger', 'SumReexCSub1m', 'SumReexLarger'
    ]  # 'SumContCAll',
    cols_dict = dict(zip(columns_list, out_col_headings))
    output_values = {}
    for col in cols_dict.items():
        output_values[col[1]] = int(sum(relevant_rows.loc[:,col[0]]))
    # print(output_values)

    top_countries_list = []
    for i, n in relevant_rows.iterrows():
        top_countries_list.append({'Country': n['Destination'], 'Value': int(n['VSmalls'] + n['VLarges'])})
#     print(top_countries_list)
    top_countries_list.sort(key=lambda tup: tup['Value'], reverse=True)
    print(top_countries_list[:10])
    output_values['top_countries_list'] = top_countries_list[:10]

    DF_CN = pandas.read_csv(DBS_PATH+'2017_CN.txt', sep='\t', 
        encoding='utf-16', warn_bad_lines=True)
    output_values['ProdName'] = utils.get_desc_by_CN(DF_CN, str(desc)[:-1]
        )['Self-Explanatory text (English)'].values[0]  # str(desc)
    print(output_values)

    # output_values = [int(sum(relevant_rows.loc[:,col])) for col in columns_list]

    # out_col_headings.append('Top countries')
    # top_countries_list = [n for n in relevant_rows['Destination']]
    # output_values.append(top_countries_list)

    # out_col_headings.append('ProdName')
    # output_values.append(str(desc))
    # print('giving results for', desc)
    # [print(a, b) for a, b in zip(out_col_headings, output_values)]
    return dumps(output_values)

@app.route("/descriptions")
def get_descriptions():
    code = request.args['cn1']
    global DBS_PATH
    DF_CN = pandas.read_csv(DBS_PATH+'2017_CN.txt', sep='\t', 
        encoding='utf-16', warn_bad_lines=True)
    print("checking for", code)
    tmp = utils.get_desc_by_CN(DF_CN, code
        )['Self-Explanatory text (English)'].values[0]
    return Response(dumps({"description": tmp}), mimetype="application/json")

def dir_edge_count(node, direction):
    global NETX_DB
    dir_edge_list = [n for n in NETX_DB[node] if (
        NETX_DB.edge[node][n]['direction'] == direction
        ) ]
    return len(dir_edge_list)

def serialize_company(company, direction='focal'):
    global NETX_DB
    if (direction == 'focal'):
        x = len(NETX_DB[company])
    else:
        x = len(NETX_DB[company]) #dir_edge_count(company, direction) too slow
    return {
    'type': "company",
    'direction': direction,
    'size': x,
    'size_metric': 'HS code diversity',
    'name': company,
    'postcode': 'AB12 CDE',
    'rank': 0
    }

def serialize_cmdty(good, direction):
    return {
    'type': "hscode",
    'direction': direction,
    'size': len(NETX_DB[good]), #dir_edge_count(good, direction), too slow
    'size_metric': '# of companies that traded this', #({} this)'.format(direction),
    'name': good,
    'rank': 0
    }

def common_goods_traded(Gph, goods_list, direction, exclude=None):
    """
    Variant of nx.common_neighbors(G, u, v)
    Return the companies with TWO common goods
    traded in the SAME DIRECTION (import or export)
    """
    for x in goods_list:
        if x not in Gph: raise nx.NetworkXError('{} is not in the graph.'.format(x))
    
    # Returns a generator
    if (len(goods_list) == 1):
        u = goods_list[0]
        return (
            x for x in Gph[u] if (
                (x is not u) and
                (Gph.edge[u][x]['direction'] == direction) and
                (x != exclude)
                )
            )
    elif (len(goods_list) == 2):
        u, v = goods_list
        return (
            x for x in Gph[u] if (
                (x in Gph[v]) and 
                (x not in (u, v)) and
                (Gph.edge[u][x]['direction'] == direction) and
                (Gph.edge[v][x]['direction'] == direction) and
                (x != exclude)
                )
            )
    elif (len(goods_list) == 3):
        u, v, w = goods_list
        return (
            x for x in Gph[u] if (
                (x in Gph[v]) and
                (x in Gph[w]) and
                (x not in (u, v, w)) and
                (
                    (Gph.edge[u][x]['direction'] == direction) and
                    (Gph.edge[v][x]['direction'] == direction) and
                    (Gph.edge[w][x]['direction'] == direction) 
                ) and
                (x != exclude)
                )
            )
    else:
        raise NotImplementedError
    

def _get_top_edges(Gph, company, howmany=None):
    """
    Commodities with the most months: returns sorted list of (u, v, data)
    """
    if company in Gph:
        all_edges = Gph.edges(nbunch=[company], data=True)
        sorted_edges = sorted(
            all_edges, 
            key=lambda tup: int(tup[2]['monthcount']),
            reverse=True
            )
        if howmany is None:
            return sorted_edges
        elif len(sorted_edges) < howmany:
            # print(company, 'only trades', Gph[company])
            return sorted_edges
        else:
            results_list = sorted_edges[:howmany]
            return results_list
    else:
        print(company, 'not in database')
        raise NotImplementedError

def _graduated_bands(total_nodes):
    """Like a tax calculator"""
    bands = [0, 20, 100, float("inf")]
    rates = [0, 0, 0.5, 0.25]
    x = 0
    prevband = 0
    for band, rate in zip(bands, rates):
        if total_nodes > band:
            x += (band - prevband) * rate
        elif total_nodes > prevband:
            x += (total_nodes - prevband) * rate
        else:
            return int(x)
        prevband = band
    return int(x)


@app.route("/graph")
def get_graph():
    """
    Returns subgraph surrounding the target company (input to be implemented)
    Subgraph contains
    -- commodities exported or imported by the target company
    -- companies that share at least the TOP [two] commodities of the target
    in each direction (top for target, not necessarily the other company)
    """
    focus_co = request.args['q']
    num_nodes = int(request.args['n'])
    node_limit = int(request.args['lim'])
    focus_co_goods_limit = _graduated_bands(node_limit)
    print('Preparing graph for {0} with {1} common goods. Limited to {2} nodes'.format(
        focus_co, num_nodes, node_limit))
    global NETX_DB
    global DBS_PATH
    DF_CN = pandas.read_csv(DBS_PATH+'2017_CN.txt', sep='\t', 
        encoding='utf-16', warn_bad_lines=True)
    nodes = []
    rels = []
    i =0
    # Add the focal company
    nodes.append(serialize_company(focus_co, direction='focal'))
    i += 1
    # Goods traded by focal company, ranked by most common first
    focal_co_goods = _get_top_edges(NETX_DB, focus_co)
    # other_goods_import = {
    #         "type": "hscode",
    #         "direction": "Imported",
    #         "size": 0,
    #         "size_metric": "Companies trading (Imported or Exported)",
    #         "name": "others"
    #         }
    # other_goods_export = {
    #         "type": "hscode",
    #         "direction": "Exported",
    #         "size": 0,
    #         "size_metric": "Companies trading (Imported or Exported)",
    #         "name": "others"
    #         }
    # TODO: add optional cut-off for weak links (low monthcount)
    # TODO: collate the minor goods into a single 'others' node
    for cmdty in focal_co_goods:
        hsnode = serialize_cmdty(good=cmdty[1], direction=cmdty[2]['direction'])
        try:
            target = nodes.index(hsnode)
        except ValueError:
            if i < focus_co_goods_limit:
                nodes.append(hsnode)
                target = i
                i += 1
        rels.append({"target": target, "source": 0})
        # print(cmdty[1], end=' ')
    # print(' ')
    # Just the top goods from focal_co_goods
    common_HS = [tup[1] for tup in _get_top_edges(NETX_DB, focus_co, howmany=num_nodes)]
    # print('checking:')
    # [print(code, utils.get_desc_by_CN(DF_CN, code)['Self-Explanatory text (English)']
    #     .values[0]) for code in common_HS]
    # Companies trading at least two goods in the SAME DIRECTION as the focal company
    importers = [name for name in common_goods_traded(NETX_DB, common_HS, 
        direction='Imported', exclude=focus_co)]
    exporters = [name for name in common_goods_traded(NETX_DB, common_HS, 
        direction='Exported', exclude=focus_co)]

    # Dummy list for finding companies that import OR export these goods
    # MAY INCLUDE GOODS NOT TRADED BY ANY RELATED COMPANIES IN THAT DIRECTION
    goods_to_show = [serialize_cmdty(n[1], 'Imported') for n in focal_co_goods]
    [goods_to_show.append(serialize_cmdty(n[1], 'Exported')) for n in focal_co_goods]
    for direction in ['Imported', 'Exported']:
        # Related companies and the goods they trade
        if (direction=='Imported'):
            names_list = importers
        else:
            names_list = exporters
        if len(names_list) != 0:  # TODO: handle case when no related companies found
            node_lim_per_name = int(
                (node_limit - focus_co_goods_limit) 
                / len(names_list)
                ) + 10
        for name in names_list:
            if i < node_limit:
                conode = serialize_company(company=name, direction=direction)
                try:
                    source = nodes.index(conode)
                except ValueError:
                    if i < node_limit:
                        nodes.append(conode)
                        source = i
                        i += 1
                for cmdty in _get_top_edges(NETX_DB, name, 
                    howmany=node_lim_per_name):
                    hsnode = serialize_cmdty(good=cmdty[1], direction=direction)
                    if hsnode in goods_to_show:
                        # check if the commodity is already there
                        # on the particular import / export side
                        try:
                            target = nodes.index(hsnode)
                        except ValueError:
                            if i < node_limit:
                                nodes.append(hsnode)
                                target = i
                                i += 1
                    rels.append({"target": target, "source": source})
    # Add node rank by size
    for r, node in enumerate(sorted(nodes, key=lambda d: int(d['size']), reverse=True)):
        node['rank'] = r

    print('Sending json for background graph with {0} nodes...'.format(str(i-1)))
    return Response(dumps({"nodes": nodes, "links": rels}),
        mimetype="application/json")

if __name__ == '__main__':
    print('Loading graph to memory...')
    NETX_DB = nx.Graph()
# DBS_PATH = 'C:\\Users\\Chris\\Parkway Drive\\Trade_finance\\Technology\\SIC_HS_tool\\'
    DBS_PATH = '/Users/ramintakin/Parkway_Drive/Trade_finance/Technology/SIC_HS_tool/'
    NETX_DB = nx.read_gml(DBS_PATH+'impex_full.graphml')
    print('loaded', NETX_DB.order(), 'nodes and', NETX_DB.size(), 'edges')
    host='127.0.0.1'
    port=8081
    print('Server running on http://{0}:{1}...'.format(host, port))
    app.run(host=host, port=port)  # , debug=True, use_reloader=False