from pages.rebalance_app_page import RebalanceApp

if __name__ == "__main__":
    json_file_path = 'portfolio_data.json'
    tickers = ['BANEP', 'SIBN', 'SMLT', 'MGNT', 'MDMG',
               'NVTK', 'ROSN', 'SBER', 'SVAV', 'TATN',
               'TRNFP', 'HEAD']
    tickers1 = ['SBER', 'LKOH']
    tickers_tdivrx = ['SBER', 'LKOH', 'X5', 'NLMK', 'TATN', 'NVTK', 'SIBN', 'ROSN', 'PLZL', 'MTSS', 'MGNT', 'TRNFP', 'SNGSP',
               'MOEX', 'HEAD', 'T', 'GMKN', 'SVCB', 'BANEP', 'BSPB', 'YDEX', 'FLOT', 'RENI', 'CHMF', 'PHOR', 'NMTP',
               'MAGN', 'MDMG', 'LSNGP', 'RTKMP', 'SMLT', 'SVAV']
    tickers_irdiv = ['IRAO', 'AQUA', 'ALRS', 'BANEP', 'BSPB', 'CHMF', 'GMKN', 'HEAD', 'LKOH',
    'LSNG', 'LSNGP', 'MDMG', 'MGNT', 'MRKC', 'MRKP', 'MSNG', 'MSRS',
    'MTSS', 'NMTP', 'NLMK', 'NVTK', 'PHOR', 'ROSN', 'RTKM', 'RTKMP',
    'SBER', 'SBERP', 'SIBN', 'SMLT', 'SNGS', 'SNGSP', 'SVAV', 'TATN',
    'TATNP', 'TRNFP', 'BELU', 'PMSB', 'MOEX', 'PLZL', 'X5']
    app = RebalanceApp(tickers_irdiv, json_file_path)
    app.run()