from django.shortcuts import render
from .forms import ExcelUploadForm
from .models import ProductSales, UploadLog
import pandas as pd
from django.http import HttpResponse
import io

# Aliases for dynamic column matching
COLUMN_ALIASES = {
    'product_name': ['product name', 'productname', 'product', 'item'],
    'sales': ['sales', 'amount', 'total', 'total_sales', 'value'],
    'date': ['date', 'transaction_date', 'sales_date']
}

# Normalize function
def normalize_column(col):
    return col.strip().lower().replace(" ", "_")

# Smart column mapper
def map_columns(df):
    normalized_cols = [normalize_column(col) for col in df.columns]
    col_mapping = {}

    for key, aliases in COLUMN_ALIASES.items():
        found = False
        for i, col in enumerate(normalized_cols):
            if col in [normalize_column(alias) for alias in aliases]:
                col_mapping[key] = df.columns[i]
                found = True
                break
        if not found:
            raise ValueError(f"Required column for '{key}' not found. Expected one of: {aliases}")
    # print("Column Mapping:", col_mapping)
    return col_mapping

# View to upload and analyze
def upload_excel(request):
    context = {}
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            file_name = excel_file.name

            # new UploadLog create
            log = UploadLog.objects.create(file_name=file_name, status='Pending')

            try:
                if file_name.endswith('.csv'):
                    df = pd.read_csv(excel_file)
                elif file_name.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(excel_file)
                else:
                    raise ValueError("Invalid file type. Please upload a .xlsx or .csv file.")

                col_mapping = map_columns(df)

                df['Product'] = df[col_mapping['product_name']]
                df['Sales'] = df[col_mapping['sales']]
                df['Date'] = pd.to_datetime(df[col_mapping['date']])

                # Save to DB without deleting old data
                for _, row in df.iterrows():
                    ProductSales.objects.create(
                        upload=log,
                        product_name=row['Product'],
                        sales=row['Sales'],
                        date=row['Date'].date()
                    )

                log.status = 'Success'
                log.save()

                df['Month'] = df['Date'].dt.to_period('M')
                
                # Calculate values for enhanced frontend
                total_sales = df.groupby('Product')['Sales'].sum().to_dict()
                avg_sales_per_month = df.groupby('Month')['Sales'].mean().to_dict()
                sales_count = df.groupby('Product')['Sales'].count().to_dict()
                
                # Additional calculations for enhanced frontend
                total_sales_sum = sum(total_sales.values())
                total_records = sum(sales_count.values())
                max_sales_value = max(total_sales.values()) if total_sales else 0
                
                # Format month names for better display
                formatted_avg_sales = {}
                for month, avg in avg_sales_per_month.items():
                    formatted_month = month.strftime('%b %Y')  # Format as "Sep 2024"
                    formatted_avg_sales[formatted_month] = round(avg, 2)

                context.update({
                    'form': form,
                    'uploaded': True,
                    'total_sales': total_sales,
                    'avg_sales_per_month': formatted_avg_sales,
                    'sales_count': sales_count,
                    'total_sales_sum': total_sales_sum,
                    'total_records': total_records,
                    'max_sales_value': max_sales_value
                })

            except Exception as e:
                log.status = 'Failed'
                log.error_message = str(e)
                log.save()
                context = {'form': form, 'error': f"Upload failed: {str(e)}"}

    else:
        form = ExcelUploadForm()

    context['form'] = form
    return render(request, 'upload.html', context)


def download_analysis(request, file_type):
    # Last successful upload
    last_upload = UploadLog.objects.filter(status='Success').last()
    if not last_upload:
        return HttpResponse("No successful uploads to download analysis.", status=404)

    # Get sales data from DB
    data_qs = ProductSales.objects.filter(upload=last_upload)
    if not data_qs.exists():
        return HttpResponse("No sales data found for last upload.", status=404)

    # Create DataFrame from DB queryset
    df = pd.DataFrame(list(data_qs.values('product_name', 'sales', 'date')))
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')

    # Prepare analysis data
    total_sales = df.groupby('product_name')['sales'].sum()
    avg_sales_month = df.groupby('month')['sales'].mean()
    sales_count = df.groupby('product_name')['sales'].count()

    # DataFrames for output
    product_analysis_df = pd.DataFrame({
        'Total Sales': total_sales,
        'Sales Count': sales_count
    }).fillna('')

    avg_sales_df = avg_sales_month.reset_index()
    avg_sales_df.columns = ['Month', 'Average Sales']

    # Export logic
    if file_type == 'xlsx':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            product_analysis_df.to_excel(writer, sheet_name='Product Analysis')
            avg_sales_df.to_excel(writer, sheet_name='Monthly Average', index=False)
        output.seek(0)

        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=analysis_result.xlsx'
        return response

    elif file_type == 'csv':
        csv_output = io.StringIO()
        product_analysis_df.to_csv(csv_output)
        csv_output.write("\n\n")
        avg_sales_df.to_csv(csv_output, index=False)

        response = HttpResponse(csv_output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=analysis_result.csv'
        return response

    else:
        return HttpResponse("Invalid file type requested.", status=400)