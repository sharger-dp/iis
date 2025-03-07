from pages.rebalance_app_page import RebalanceApp

if __name__ == "__main__":
    json_file_path = 'portfolio_data.json'
    tickers2 = ['BANEP', 'SIBN', 'SMLT', 'MGNT', 'MDMG',
               'NVTK', 'ROSN', 'SBER', 'SVAV', 'TATN',
               'TRNFP', 'HEAD']
    tickers1 = ['SBER', 'LKOH']
    tickers = ['SBER', 'LKOH', 'X5', 'NLMK', 'TATN', 'NVTK', 'SIBN', 'ROSN', 'PLZL', 'MTSS', 'MGNT', 'TRNFP', 'SNGSP',
               'MOEX', 'HEAD', 'T', 'GMKN', 'SVCB', 'BANEP', 'BSPB', 'YDEX', 'FLOT', 'RENI', 'CHMF', 'PHOR', 'NMTP',
               'MAGN', 'MDMG', 'LSNGP', 'RTKMP', 'SMLT', 'SVAV']
    app = RebalanceApp(tickers, json_file_path)
    app.run()