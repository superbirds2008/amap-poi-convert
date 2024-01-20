package main

import (
    "encoding/csv"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "os"
    "strconv"

    "github.com/spf13/cobra"
)

type GeoCode struct {
    Status  string `json:"status"`
    Info    string `json:"info"`
    Geocodes []struct {
        Location string `json:"location"`
    } `json:"geocodes"`
}

type ReGeoCode struct {
    Status   string `json:"status"`
    Info     string `json:"info"`
    Regeocode struct {
        Pois []struct {
            ID   string `json:"id"`
            Name string `json:"name"`
        } `json:"pois"`
    } `json:"regeocode"`
}

func get_location(address string, api_key string) (string, error) {
    url := "https://restapi.amap.com/v3/geocode/geo"
    resp, err := http.Get(fmt.Sprintf("%s?address=%s&output=JSON&key=%s", url, address, api_key))
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()

    var geo GeoCode
    err = json.NewDecoder(resp.Body).Decode(&geo)
    if err != nil {
        return "", err
    }

    if geo.Status == "1" {
        return geo.Geocodes[0].Location, nil
    } else {
        return "", fmt.Errorf("Error: %s - %s", resp.Status, geo.Info)
    }
}

func get_pois(location string, api_key string) ([][2]string, error) {
    url := "https://restapi.amap.com/v3/geocode/regeo"
    resp, err := http.Get(fmt.Sprintf("%s?location=%s&output=JSON&key=%s&extensions=all", url, location, api_key))
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var regeo ReGeoCode
    err = json.NewDecoder(resp.Body).Decode(&regeo)
    if err != nil {
        return nil, err
    }

    if regeo.Status == "1" {
        pois := make([][2]string, len(regeo.Regeocode.Pois))
        for i, poi := range regeo.Regeocode.Pois {
            pois[i] = [2]string{poi.ID, poi.Name}
        }
        return pois, nil
    } else {
        return nil, fmt.Errorf("Error: %s - %s", resp.Status, regeo.Info)
    }
}

func process_csv(cmd *cobra.Command, args []string) {
    // 解析 args 并处理错误
    inputFile, err := os.Open(args[0])
    if err != nil {
        fmt.Println("Error opening input file:", err)
        return
    }
    defer inputFile.Close()

    apiKey := args[1]

    startLine, err := strconv.Atoi(args[2])
    if err != nil {
        fmt.Println("Error parsing start line:", err)
        return
    }

    endLine, err := strconv.Atoi(args[3])
    if err != nil {
        fmt.Println("Error parsing end line:", err)
        return
    }

    // 调用你的原始 process_csv 函数并处理错误
    err = process_csv(inputFile, apiKey, startLine, endLine)
    if err != nil {
        fmt.Println("Error processing CSV:", err)
    }
}

func main() {
    var cmdProcessCSV = &cobra.Command{
        Use:   "process_csv [input_file] [output_file] [api_key] [start_line] [end_line]",
        Short: "Process a CSV file with addresses using the AMap API",
        Long:  `Process a CSV file with addresses using the AMap API and write the POIs to the output CSV file.`,
        Args:  cobra.ExactArgs(5),
        Run:   process_csv,
    }

    var rootCmd = &cobra.Command{Use: "app"}
    rootCmd.AddCommand(cmdProcessCSV)
    rootCmd.Execute()
}