from pages.rebalance_app_page import RebalanceApp

if __name__ == "__main__":
    tickers = ['BANEP', 'SIBN', 'SMLT', 'MGNT', 'MDMG',
               'NVTK', 'ROSN', 'SBER', 'SVAV', 'TATN',
               'TRNFP', 'HEAD']
    tickers_test = ['SBER', 'LKOH', 'X5', 'NLMK', 'TATN']
    tickers_div = ['SBER', 'LKOH', 'X5', 'NLMK', 'TATN', 'NVTK', 'SIBN', 'ROSN', 'PLZL', 'MTSS', 'MGNT', 'TRNFP', 'SNGSP',
               'MOEX', 'HEAD', 'T', 'GMKN', 'SVCB', 'BANEP', 'BSPB', 'YDEX', 'FLOT', 'RENI', 'CHMF', 'PHOR', 'NMTP',
               'MAGN', 'MDMG', 'LSNGP', 'RTKMP', 'SMLT', 'SVAV']
    app = RebalanceApp(tickers)
    app.run()