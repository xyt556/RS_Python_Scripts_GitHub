
####################### Validation.py #######################

############################
####### DESCRIPTION ########
############################

#
# Created by Grace Kuiper, 1/15/19
#
# Script Description:
#      This script will generate the layers and tables necessary for the hybrid model validation. There are
#      three primary methods for the validation: Buffer Capture, Grid Density, and Ellipse Overlap.
#
# This was edited by David South to run for the counties that were added later on.
#       New counties: Kings, California / Stanislaus, California / Sussex, Delaware / Kent, Delaware
#

########################################
##################SETUP#################
########################################

#            #             #           #
############Import Libraries############
#            #             #           #

import os
import sys
import csv
import arcpy

sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\RS_Python_Scripts_GitHub')

from Automated_Review import find_FIPS_UTM

arcpy.env.OverwriteOutput = True

#            #             #           #
############Define Variables############
#            #             #           #

# Results will be saved to a folder titled "Validation_Results", which contains geodatabases called "AutoReviewCounties",
# "Dist_Between_Tables", "Buffers", "Buffer_Capture","Fishnets",and "Grid_Density" to hold layers with hybrid model points,
# near tables with distances between barns, ground truth buffers, spatial join outputs for hybrid model points in ground
# truth buffer zones, fishnet grids, and spatial join outputs for hybrid model points in fishnet grids, respectively. Also
# create a folder called "TP_FN_Counties" for shape files for ground truth points.

# Set up variables for file paths to the geodatabases and files in the "Validation_Results" folder, as well as the
# pathways to source data (hybrid model results, ground truth results, and the county outlines).

#########Change these Variables#########
State_Name = 'Arkansas' 
State_Abbrev = 'AR' 
County_Name = 'Cluster' 

##########Keep these Variables##########
CountyOutlinesPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Cluster_Outlines.gdb/'

TP_FNPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\TP_FN_Counties/' # added the four coutnies. Hopefully it won't matter that the fields are different than the rest.
AutoReviewPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\AutoReviewCounties.gdb/' # Don't add counties to this GDB, it is populated automatically.
NearTablePath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Dist_Between_Tables.gdb/'
BuffersPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Buffers.gdb/'
Buffer_CapturePath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Buffer_Capture.gdb/'
FishnetsPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Fishnets.gdb/'
Grid_DensityPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Grid_Density.gdb/'
FLAPSPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\FLAPS.gdb/'
Cell_AssignmentsPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Cell_Assignments.gdb/'
EllipsePath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Ellipse.gdb/'

#            #             #           #
#############Define Functions###########
#            #             #           #

def tableToCSV(Input_Table, Filepath):
    Field_List = arcpy.ListFields(Input_Table)
    Field_Names = [Field.name for Field in Field_List]
    with open(Filepath, 'wb') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(Field_Names)
        with arcpy.da.SearchCursor(Input_Table, Field_Names) as cursor:
            for row in cursor:
                writer.writerow(row)
        print Filepath + " CREATED"
    csv_file.close()
    
#            #             #           #
#############Get Source Data############
#            #             #           #

# Pull ground truth points, hybrid model points, and county outlines from their sources.

County_Outline = County_Name + 'Co' + State_Abbrev + '_outline'
TP_FN = State_Abbrev + '_' + County_Name + '_TP_FN'
AutoReview = State_Abbrev + '_' + County_Name + '_AutoReview'
FLAPS = State_Abbrev + '_' + County_Name + '_FLAPS'
source_data_list = {CountyOutlinesPath + County_Outline : County_Outline,\
                    TP_FNPath + TP_FN + '.shp': TP_FN,\
                    AutoReviewPath + AutoReview : AutoReview,\
                    FLAPSPath + FLAPS : FLAPS}

for source_data in source_data_list:
    if arcpy.Exists(source_data):
        arcpy.MakeFeatureLayer_management(source_data,source_data_list[source_data])
    else:
        print ("Error: source layer does not exist.", source_data)

print("source layers created")      
      
########################################
##############GRID DENSITY##############
########################################
 
# Generate a grid to fit the county outline with cell sizes of listed in Grid_Size_List variable. Then
# use "Spatial Join" tool to count the number of hybrid model and ground truth points within each grid
# cell, for each cell size. Save the spatial join outputs to the "Grid_Density" geodatabase.
fishnet_coord = arcpy.Describe(County_Outline)

Fishnet = State_Abbrev + '_' + County_Name + '_Fishnet_'
Grid_Size_List = ['500','1000','1500','2000','2500','3000','4000','5000','6000','7000','8000','9000','10000','11000','12000','13000','14000','15000',\
                  '16000','17000','18000','19000','20000','22000','25000','30000','35000','40000','45000','50000','55000','60000']
for Grid_Size in Grid_Size_List:
   if arcpy.Exists(FishnetsPath + Fishnet + Grid_Size) == True:
      print ("fishnet of " + Grid_Size + " meters for " + County_Name + " county already exists")
   else:
      arcpy.CreateFishnet_management(FishnetsPath + Fishnet + Grid_Size,str(fishnet_coord.extent.lowerLeft),\
                                     str(fishnet_coord.extent.XMin) + " " + str(fishnet_coord.extent.YMax),\
                                     Grid_Size, Grid_Size, "", "", str(fishnet_coord.extent.upperRight), "NO_LABELS",County_Outline,"POLYGON")
      print(Grid_Size + "-meter fishnet created for " + County_Name + " county")            

Grid_Densities = [] 
Input_List = {AutoReviewPath+AutoReview:AutoReview,TP_FNPath+TP_FN+".shp":TP_FN,FLAPSPath+FLAPS:FLAPS}
for Data_Type in Input_List:
   for Grid_Size in Grid_Size_List:
      if arcpy.Exists(Grid_DensityPath + Input_List[Data_Type] + '_Grid_' + Grid_Size) == True:
         print ("grid density analysis for " + Grid_Size + " meters already complete")
      else:
         arcpy.SpatialJoin_analysis(FishnetsPath + Fishnet + Grid_Size,Data_Type,Grid_DensityPath + Input_List[Data_Type] + '_Grid_' + Grid_Size,\
                           "JOIN_ONE_TO_ONE","KEEP_ALL","","COMPLETELY_CONTAINS","","")
         print("grid density calculated for " + Grid_Size + " meters")
      Grid_Densities.append(Input_List[Data_Type] + '_Grid_' + Grid_Size)

# Export spatial join outputs (from calculating grid density with fishnet layer), to .csv geodatabase.
Grid_Density_CSVPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Grid_Density/'

for Grid_Density in Grid_Densities:
   if arcpy.Exists(Grid_Density_CSVPath + Grid_Density)== False:
      tableToCSV(Grid_DensityPath + Grid_Density,Grid_Density_CSVPath + Grid_Density + '.csv')

########################################
#############ELLIPSE OVERLAP############
########################################

def findField(fc, fi): # David South added this function so that the script
                       # can check to see if a field exists in the data.
  fieldnames = [field.name for field in arcpy.ListFields(fc)]
  if fi in fieldnames:
    return True
  else:
    return False

# Construct standard deviational ellipses within grid sizes of 3, 10, and 20km. First spatial join layers
# to fishnet polygons to assign cell ID to points for hybrid and FLAPS models and ground truth layer.
Ellipse_Size_List = ['3000','10000','20000']

Ellipses = []
for Data_Type in Input_List:
   for Ellipse_Size in Ellipse_Size_List:
      if arcpy.Exists(Cell_AssignmentsPath + Input_List[Data_Type] + '_Cell_' + Ellipse_Size) == True:
         Ellipses.append(Input_List[Data_Type] + '_Ellipse_' + Ellipse_Size)
         print ("ellipse of " + Ellipse_Size + " size for " + Input_List[Data_Type] + " in " + County_Name + " county already exists")
      else:
         arcpy.MakeFeatureLayer_management(Grid_DensityPath + Input_List[Data_Type] + '_Grid_' + Ellipse_Size,Input_List[Data_Type] + '_Grid_' + Ellipse_Size)
         arcpy.AddField_management(FishnetsPath + Fishnet + Ellipse_Size, "Cell_ID","LONG","","","","","NULLABLE","NON_REQUIRED","")
         if findField(FishnetsPath + Fishnet + Ellipse_Size, "OID") is True:  # This section added to allow for inputs with OBJECTID instead of just OID
             arcpy.CalculateField_management(FishnetsPath + Fishnet + Ellipse_Size, "Cell_ID", "sum([!OID!],0)","PYTHON","")
         elif findField(FishnetsPath + Fishnet + Ellipse_Size, "OBJECTID") is True:
             print "File for", Fishnet + Ellipse_Size, "had OBJECTID field instead of OID, but no matter it works fine."
             arcpy.CalculateField_management(FishnetsPath + Fishnet + Ellipse_Size, "Cell_ID", "sum([!OBJECTID!],0)","PYTHON","")
         arcpy.SelectLayerByAttribute_management(Input_List[Data_Type] + '_Grid_' + Ellipse_Size,"NEW_SELECTION","Join_Count > 2")
         arcpy.SelectLayerByLocation_management(Input_List[Data_Type],"COMPLETELY_WITHIN",Input_List[Data_Type] + '_Grid_' + Ellipse_Size,"","NEW_SELECTION")
         count = int(arcpy.GetCount_management(Input_List[Data_Type]).getOutput(0))
         if count < 1:
            print("too few points for ellipse of " + Ellipse_Size + " size for " + Input_List[Data_Type] + " in " + County_Name + " county")
         else:
            arcpy.SpatialJoin_analysis(Input_List[Data_Type],FishnetsPath + Fishnet + Ellipse_Size,Cell_AssignmentsPath + Input_List[Data_Type] + '_Cell_' + Ellipse_Size,\
                                 "JOIN_ONE_TO_ONE","KEEP_ALL","", "COMPLETELY_WITHIN", "","")
            arcpy.DirectionalDistribution_stats(Cell_AssignmentsPath + Input_List[Data_Type] + '_Cell_' + Ellipse_Size, EllipsePath + Input_List[Data_Type] + '_Ellipse_' + Ellipse_Size,\
                                          "1_STANDARD_DEVIATION", "", "Cell_ID")
            print ("ellipse of " + Ellipse_Size + "size for " + Input_List[Data_Type] + " in " + County_Name + "county created")
            Ellipses.append(Input_List[Data_Type] + '_Ellipse_' + Ellipse_Size)

# Create new layer of intersection between FLAPS and hybrid model ellipses at 3, 19, and 20 km and ground
# ground truth ellipses.
Model_List = {AutoReviewPath + AutoReview:AutoReview,FLAPSPath + FLAPS:FLAPS}
for Model_Type in Model_List:
   for Ellipse_Size in Ellipse_Size_List:
      if arcpy.Exists(EllipsePath + TP_FN + '_Ellipse_' + Ellipse_Size)== False:
         print ("no ground truth ellipses exist for " + County_Name + " county at " + Ellipse_Size + " size")
      else:
         if arcpy.Exists(EllipsePath + Model_List[Model_Type] + '_Ellipse_' + Ellipse_Size)== False:
            print ("there is no " +Model_List[Model_Type] + " ellipse at " + Ellipse_Size + " size")
         else:
            if arcpy.Exists(EllipsePath + Model_List[Model_Type] + '_Intersection_' + Ellipse_Size)==True:
               print ("intersection between " + Model_List[Model_Type]+ " and ground truth at " + Ellipse_Size + " size already exists")
               Ellipses.append(Model_List[Model_Type] + '_Intersection_' + Ellipse_Size)
            else:
               arcpy.Intersect_analysis ([EllipsePath + Model_List[Model_Type] + '_Ellipse_' + Ellipse_Size,EllipsePath + TP_FN + '_Ellipse_' + Ellipse_Size],\
                                  EllipsePath + Model_List[Model_Type] + '_Intersection_' + Ellipse_Size,"ALL","","INPUT")
               Ellipses.append(Model_List[Model_Type] + '_Intersection_' + Ellipse_Size)
               print("intersection at " + Ellipse_Size + " size made between " + Model_List[Model_Type] + " ellipse and ground truth ellipse")
 
# Export ellipse and intersection outputs to .csv files.
Ellipse_CSVPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Ellipses/'

for Ellipse in Ellipses:
   if arcpy.Exists(EllipsePath + Ellipse)== False:
      tableToCSV(EllipsePath + Ellipse,Ellipse_CSVPath + Ellipse + '.csv')
  

#########################################################################################################
#########################################################################################################
# Generate buffers around ground truth points of 100, 500, 1000, 2000, and 5000 meters. Then use the
# "Spatial Join" tool to count the number of hybrid model points that fall within each buffer, for each
# radius size. Save the spatial join outputs to the "Buffer_Capture" geodatabase.

Captures = []
Buffer_Size_List = ['100','500','1000','2000','5000']
for Buffer_Size in Buffer_Size_List:
   arcpy.Buffer_analysis(TP_FNPath + TP_FN + ".shp",BuffersPath + State_Abbrev + '_' + County_Name + '_Buffer_' + Buffer_Size,\
                         Buffer_Size,"FULL","","NONE","","PLANAR")
   for Model_Type in Model_List:
      arcpy.SpatialJoin_analysis(BuffersPath + State_Abbrev + '_' + County_Name + '_Buffer_' + Buffer_Size,\
                                 Model_Type,Buffer_CapturePath + Model_List[Model_Type] + '_Capture_' + Buffer_Size,\
                                 "JOIN_ONE_TO_ONE","KEEP_ALL","","COMPLETELY_CONTAINS","","")
      Captures.append(Model_List[Model_Type] + '_Capture_' + Buffer_Size)

print ("buffer captures finished")
#########################################################################################################
# Export distance between farms tables to .csv files.

Buffer_Capture_CSVPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Buffer_Capture/'

for Capture in Captures:
   tableToCSV(Buffer_CapturePath + Capture,Buffer_Capture_CSVPath + Capture + '.csv')
  