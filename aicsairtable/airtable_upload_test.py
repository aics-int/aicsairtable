from argolight_power import ArgoPowerMetrics

file_path = "/allen/aics/microscopy/brian_whitney/ZSD0_argo_10x_slide0_20210619_2021_06_19 at 16_39_16.csv"
env_vars = "/allen/aics/microscopy/brian_whitney/repos/aicsairtable/.env"

ArgoPower = ArgoPowerMetrics(file_path=file_path)
ArgoPower.upload(env_vars=env_vars)
